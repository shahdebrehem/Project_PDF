<?php

use App\Http\Controllers\Auth\AuthController;
use Illuminate\Container\Attributes\Auth;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\SettingsController;


Route::post('/auth/signup', [AuthController::class, 'signup']);
Route::post('/auth/login', [AuthController::class, 'login']);

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/auth/logout', [AuthController::class, 'logout']);
});

Route::get('/me', [AuthController::class, 'me'])->middleware('auth:sanctum');

Route::prefix('auth')->group(function () {
    Route::post('/refresh', [AuthController::class, 'refresh'])
        ->middleware('auth:sanctum');
});


Route::post('/auth/forgot-password', [AuthController::class, 'forgotPassword']);
Route::post('/auth/reset-password', [AuthController::class, 'resetPassword']);

Route::middleware('auth:sanctum')->get('/me', [AuthController::class, 'me']);
Route::middleware('auth:sanctum')->put('/me', [AuthController::class, 'updateProfile']);



Route::middleware('auth:sanctum')->prefix('settings')->group(function () {
    Route::put('/language', [SettingsController::class, 'changeLanguage']);
});

Route::middleware('auth:sanctum')->prefix('settings')->group(function () {
    Route::put('/theme', [SettingsController::class, 'changeTheme']);
});

Route::middleware('auth:sanctum')->prefix('settings')->group(function () {
    Route::put('/password', [SettingsController::class, 'changePassword']);
});