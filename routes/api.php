<?php

use App\Http\Controllers\Auth\AuthController;
use App\Http\Controllers\FilesController;
use App\Http\Controllers\SettingsController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Auth Routes (Public)
|--------------------------------------------------------------------------
*/
Route::post('/auth/signup',          [AuthController::class, 'signup']);
Route::post('/auth/login',           [AuthController::class, 'login']);
Route::post('/auth/forgot-password', [AuthController::class, 'forgotPassword']);
Route::post('/auth/reset-password',  [AuthController::class, 'resetPassword']);

/*
|--------------------------------------------------------------------------
| Files Routes (Public)
|--------------------------------------------------------------------------
*/
Route::get('/files',         [FilesController::class, 'recent']);
Route::post('/files/upload', [FilesController::class, 'upload']);
Route::delete('/files/{id}', [FilesController::class, 'destroy']);

/*
|--------------------------------------------------------------------------
| Protected Routes (JWT)
|--------------------------------------------------------------------------
*/
Route::middleware('auth:api')->group(function () {

    // Auth
    Route::post('/auth/logout',  [AuthController::class, 'logout']);
    Route::post('/auth/refresh', [AuthController::class, 'refresh']);

    // Profile
    Route::get('/me',  [AuthController::class, 'me']);
    Route::put('/me',  [AuthController::class, 'updateProfile']);

    // Settings
    Route::prefix('settings')->group(function () {
        Route::put('/language', [SettingsController::class, 'changeLanguage']);
        Route::put('/theme',    [SettingsController::class, 'changeTheme']);
        Route::put('/password', [SettingsController::class, 'changePassword']);
    });

    // PDF Processing
    Route::post('/files/process',     [FilesController::class, 'process']);
    Route::get('/files/{id}/results', [FilesController::class, 'results']);
});