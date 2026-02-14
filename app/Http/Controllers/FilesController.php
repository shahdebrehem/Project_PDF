<?php

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
            ->take(5)
            ->get(['id', 'name', 'type', 'created_at']);

        return response()->json([
            'data' => $files
        ]);
    }

    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|mimes:pdf|max:10240',
        ]);

        $path = $request->file('file')->store('pdfs', 'public');

        $file = File::create([
            'user_id' => auth()->id(),
            'name' => $request->file('file')->getClientOriginalName(),
            'type' => 'PDF',
            'path' => $path,
        ]);

        return response()->json([
            'message' => 'File uploaded successfully',
            'file' => $file,
        ]);
    }
}
