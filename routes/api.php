<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\FilesController;
use App\Http\Controllers\Auth\AuthController;
use App\Http\Controllers\SettingsController;

/*
|--------------------------------------------------------------------------
| Auth Routes
|--------------------------------------------------------------------------
*/

Route::post('/auth/signup', [AuthController::class, 'signup']);
Route::post('/auth/login', [AuthController::class, 'login']);
Route::post('/auth/forgot-password', [AuthController::class, 'forgotPassword']);
Route::post('/auth/reset-password', [AuthController::class, 'resetPassword']);

/*
|--------------------------------------------------------------------------
| Protected Routes (Sanctum)
|--------------------------------------------------------------------------
*/

Route::middleware('auth:sanctum')->group(function () {

    // Auth
    Route::post('/auth/logout', [AuthController::class, 'logout']);
    Route::post('/auth/refresh', [AuthController::class, 'refresh']);

    // Profile
    Route::get('/me', [AuthController::class, 'me']);
    Route::put('/me', [AuthController::class, 'updateProfile']);

    // Settings
    Route::prefix('settings')->group(function () {
        Route::put('/language', [SettingsController::class, 'changeLanguage']);
        Route::put('/theme', [SettingsController::class, 'changeTheme']);
        Route::put('/password', [SettingsController::class, 'changePassword']);
    });

    // Files
    Route::get('/files/recent', [FilesController::class, 'recent']);
    Route::post('/files/upload', [FilesController::class, 'upload']);
});
