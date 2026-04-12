<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\File;
use App\Models\Summary;
use App\Models\Question;
use App\Models\Translation;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\Process\Process;

class FilesController extends Controller
{
    // ✏️ غيّر المسار ده لمسار السكريبت عندك
    const SCRIPT_PATH = '/home/hany/Grad/Project_PDF/ai/pdf_agent_suite.py';
    const OUTPUT_DIR  = '/home/hany/Grad/Project_PDF/ai/pdf_output';

    // ────────────────────────────────────────────────────────
    //  GET /files  — آخر 10 ملفات للـ user
    // ────────────────────────────────────────────────────────
    public function recent()
    {
        if (!auth()->check()) {
            return response()->json(['success' => true, 'data' => []]);
        }

        $files = File::where('user_id', auth()->id())
            ->latest()
            ->take(10)
            ->get();

        return response()->json([
            'success' => true,
            'data'    => $files->map(fn($f) => $this->formatFile($f)),
        ]);
    }

    // ────────────────────────────────────────────────────────
    //  POST /files/upload  — رفع PDF بس (بدون معالجة)
    // ────────────────────────────────────────────────────────
    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|mimes:pdf|max:51200',
        ]);

        $file   = $request->file('file');
        $userId = auth()->id();
        $folder = $userId ? 'pdfs/' . $userId : 'pdfs/guest';
        $path   = $file->store($folder, 'public');

        $savedFile = File::create([
            'user_id'     => $userId,
            'file_name'   => $file->getClientOriginalName(),
            'file_type'   => 'PDF',
            'file_path'   => $path,
            'size'        => $file->getSize(),
            'status'      => 'Uploaded',
            'uploaded_at' => now(),
        ]);

        return response()->json([
            'success' => true,
            'message' => 'File uploaded successfully',
            'data'    => $this->formatFile($savedFile),
        ]);
    }

    // ────────────────────────────────────────────────────────
    //  POST /files/process  — رفع PDF ومعالجته بالـ Python
    //  Body (form-data):
    //    file      : PDF (required)
    //    mode      : all | summarize | questions | translate | extract
    //    page_from : int (optional)
    //    page_to   : int (optional)
    //    lang      : ar | en | auto (optional, default: auto)
    // ────────────────────────────────────────────────────────
    public function process(Request $request)
{
    $request->validate([
        'file'      => 'required_without:file_id|mimes:pdf|max:51200',
        'file_id'   => 'required_without:file|string',
        'mode'      => 'sometimes|in:all,summarize,questions,translate,extract',
        'page_from' => 'sometimes|integer|min:1',
        'page_to'   => 'sometimes|integer|min:1',
        'lang'      => 'sometimes|in:ar,en,auto',
    ]);

    $mode     = $request->input('mode', 'all');
    $pageFrom = $request->input('page_from');
    $pageTo   = $request->input('page_to');
    $lang     = $request->input('lang', 'auto');
    $userId   = auth()->id();

    // ── لو في file_id استخدم الملف المرفوع قبل كده ────────
    if ($request->has('file_id')) {
        $savedFile = File::find($request->input('file_id'));
        if (!$savedFile) {
            return response()->json(['success' => false, 'message' => 'File not found'], 404);
        }
        $fullPath = storage_path('app/public/' . $savedFile->file_path);
        $originalName = $savedFile->file_name;
    } else {
        $file    = $request->file('file');
        $folder  = $userId ? 'pdfs/' . $userId : 'pdfs/guest';
        $path    = $file->store($folder, 'public');
        $fullPath = storage_path('app/public/' . $path);
        $originalName = $file->getClientOriginalName();

        $savedFile = File::create([
            'user_id'     => $userId,
            'file_name'   => $originalName,
            'file_type'   => 'PDF',
            'file_path'   => $path,
            'size'        => $file->getSize(),
            'status'      => 'Processing',
            'uploaded_at' => now(),
        ]);
    }

    // ── لو النتايج موجودة قبل كده ارجعها مباشرة ──────────
    if ($mode === 'summarize') {
        $existing = Summary::where('file_id', (string)$savedFile->id)->latest()->first();
        if ($existing) {
            return response()->json([
                'success' => true,
                'message' => 'Results retrieved from cache',
                'data'    => ['file' => $this->formatFile($savedFile), 'results' => ['summary' => $existing->content]],
            ]);
        }
    }
    if ($mode === 'questions') {
        $existing = Question::where('file_id', (string)$savedFile->id)->latest()->first();
        if ($existing) {
            return response()->json([
                'success' => true,
                'message' => 'Results retrieved from cache',
                'data'    => ['file' => $this->formatFile($savedFile), 'results' => ['questions' => $existing->question]],
            ]);
        }
    }
    if ($mode === 'translate') {
        $existing = Translation::where('file_id', (string)$savedFile->id)->latest()->first();
        if ($existing) {
            return response()->json([
                'success' => true,
                'message' => 'Results retrieved from cache',
                'data'    => ['file' => $this->formatFile($savedFile), 'results' => ['translation' => $existing->translated_text]],
            ]);
        }
    }

    // ── تشغيل السكريبت ────────────────────────────────────
    $savedFile->update(['status' => 'Processing']);

    $cmd = [
        'python3', self::SCRIPT_PATH,
        '--pdf',  $fullPath,
        '--mode', $mode,
        '--lang', $lang,
    ];

    if ($pageFrom && $pageTo) {
        array_push($cmd, '--page-from', (string)$pageFrom, '--page-to', (string)$pageTo);
    }

    $process = new Process($cmd);
    $process->setTimeout(600);
    $process->run();

    if (!$process->isSuccessful()) {
        $savedFile->update(['status' => 'Failed']);
        return response()->json([
            'success' => false,
            'message' => 'Processing failed',
            'error'   => $process->getErrorOutput(),
        ], 500);
    }

    // ── قراءة النتايج وحفظها في MongoDB ──────────────────
    $pdfName = pathinfo($originalName, PATHINFO_FILENAME);
    $outDir  = self::OUTPUT_DIR . '/' . $pdfName;
    $result  = [];

    $summaryPath = $outDir . '/SUMMARY.md';
    if (file_exists($summaryPath) && in_array($mode, ['all', 'summarize'])) {
        $content = file_get_contents($summaryPath);
        Summary::create(['user_id' => $userId, 'file_id' => (string)$savedFile->id, 'content' => $content]);
        $result['summary'] = $content;
    }

    $questionsPath = $outDir . '/QUESTIONS.md';
    if (file_exists($questionsPath) && in_array($mode, ['all', 'questions'])) {
        $content = file_get_contents($questionsPath);
        Question::create(['user_id' => $userId, 'file_id' => (string)$savedFile->id, 'question' => $content, 'answer' => '']);
        $result['questions'] = $content;
    }

    $translationPath = $outDir . '/TRANSLATED.md';
    if (file_exists($translationPath) && in_array($mode, ['all', 'translate'])) {
        $content = file_get_contents($translationPath);
        Translation::create(['user_id' => $userId, 'file_id' => (string)$savedFile->id, 'translated_text' => $content, 'target_language' => $lang]);
        $result['translation'] = $content;
    }

    $extractedPath = $outDir . '/EXTRACTED.md';
    if (file_exists($extractedPath)) {
        $result['extracted'] = file_get_contents($extractedPath);
    }

    $savedFile->update(['status' => 'Completed']);

    return response()->json([
        'success' => true,
        'message' => 'Processing completed',
        'data'    => ['file' => $this->formatFile($savedFile->fresh()), 'results' => $result],
    ]);
}
    // ────────────────────────────────────────────────────────
    //  GET /files/{id}/results  — نتايج ملف معين
    // ────────────────────────────────────────────────────────
    public function results($id)
    {
        $file = File::where('user_id', auth()->id())->findOrFail($id);

        return response()->json([
            'success' => true,
            'data'    => [
                'file'        => $this->formatFile($file),
                'summary'     => Summary::where('file_id', (string)$file->id)->latest()->first()?->content,
                'questions'   => Question::where('file_id', (string)$file->id)->latest()->first()?->question,
                'translation' => Translation::where('file_id', (string)$file->id)->latest()->first()?->translated_text,
            ],
        ]);
    }

    // ────────────────────────────────────────────────────────
    //  DELETE /files/{id}
    // ────────────────────────────────────────────────────────
    public function destroy($id)
    {
        if (!auth()->check()) {
            return response()->json(['success' => false, 'message' => 'Unauthenticated.'], 401);
        }

        $file = File::where('user_id', auth()->id())->findOrFail($id);
        Storage::disk('public')->delete($file->file_path);

        // حذف النتايج المرتبطة
        Summary::where('file_id', (string)$file->id)->delete();
        Question::where('file_id', (string)$file->id)->delete();
        Translation::where('file_id', (string)$file->id)->delete();

        $file->delete();

        return response()->json(['success' => true, 'message' => 'File deleted successfully']);
    }

    // ────────────────────────────────────────────────────────
    //  Helpers
    // ────────────────────────────────────────────────────────
    private function formatFile($file): array
    {
        return [
            'id'     => (string) $file->id,
            'name'   => $file->file_name,
            'type'   => $file->file_type ?? 'PDF',
            'status' => $file->status ?? 'Completed',
            'size'   => $this->formatBytes($file->size ?? 0),
            'date'   => $file->uploaded_at?->format('M d, Y')
                     ?? $file->created_at?->format('M d, Y')
                     ?? 'Unknown',
        ];
    }

    private function formatBytes($bytes, $precision = 2): string
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        $bytes = max($bytes, 0);
        $pow   = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow   = min($pow, count($units) - 1);
        $bytes /= pow(1024, $pow);
        return round($bytes, $precision) . ' ' . $units[$pow];
    }
}