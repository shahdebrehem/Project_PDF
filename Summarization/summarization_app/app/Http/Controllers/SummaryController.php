<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class SummaryController extends Controller
{
    public function summarize(Request $request)
    {
        $response = Http::timeout(120)->post(
            'http://127.0.0.1:8001/summarize', 
            [
                'text' => $request->text
            ]
        );

        return response()->json($response->json());
    }
}
