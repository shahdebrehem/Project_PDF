<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

use App\Http\Controllers\SummaryController;

Route::post('/summarize', [SummaryController::class, 'summarize']);
