<?php
// app/Http/Controllers/FilesController.php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\File;
use Illuminate\Support\Facades\Storage;

class FilesController extends Controller
{
    public function recent()
    {
        $files = File::where('user_id', auth()->id())
            ->latest()
            ->take(10)
            ->get();

        return response()->json([
            'success' => true,
            'data' => $files->map(function ($file) {
                return [
                    'id' => (string) $file->id,
                    'name' => $file->name,
                    'type' => $file->type ?? 'Summary',
                    'status' => $file->status ?? 'Completed', // إضافة status
                    'size' => $this->formatBytes($file->size ?? 0), // إضافة size
                    'created_at' => $file->created_at?->diffForHumans() ?? 'Recently',
                    'date' => $file->created_at?->format('M d, Y') ?? 'Unknown',
                ];
            })
        ]);
    }

    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|mimes:pdf|max:10240',
        ]);

        $file = $request->file('file');
        $path = $file->store('pdfs/' . auth()->id(), 'public');

        $savedFile = File::create([
            'user_id' => auth()->id(),
            'name' => $file->getClientOriginalName(),
            'type' => $request->input('type', 'Summary'),
            'path' => $path,
            'size' => $file->getSize(),
            'status' => 'Completed',
        ]);

        return response()->json([
            'success' => true,
            'message' => 'File uploaded successfully',
            'data' => [
                'id' => (string) $savedFile->id,
                'name' => $savedFile->name,
                'type' => $savedFile->type,
                'status' => $savedFile->status,
                'size' => $this->formatBytes($savedFile->size),
                'created_at' => $savedFile->created_at->diffForHumans(),
                'date' => $savedFile->created_at->format('M d, Y'),
            ]
        ]);
    }

    public function destroy($id)
    {
        $file = File::where('user_id', auth()->id())->findOrFail($id);
        
        // حذف الملف من التخزين
        Storage::disk('public')->delete($file->path);
        
        // حذف من قاعدة البيانات
        $file->delete();

        return response()->json([
            'success' => true,
            'message' => 'File deleted successfully'
        ]);
    }

    private function formatBytes($bytes, $precision = 2)
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        
        $bytes /= pow(1024, $pow);
        
        return round($bytes, $precision) . ' ' . $units[$pow];
    }
}