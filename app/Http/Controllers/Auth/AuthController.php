<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Mail;

class AuthController extends Controller
{
    public function signup(Request $request)
    {
        $data = $request->validate([
            'name' => ['required','string','max:255'],
            'email' => ['required','email','max:255','unique:users,email'],
            'password' => ['required','string','min:8','confirmed'],
        ]);

        $user = User::create([
            'name' => $data['name'],
            'email' => $data['email'],
            'password' => Hash::make($data['password']),
        ]);

        $token = $user->createToken('api')->plainTextToken;

        return response()->json([
            'success' => true,
            'message' => 'Registered successfully',
            'data' => [
                'token' => $token,
                'user' => [
                    'id' => (string) $user->id,
                    'name' => $user->name,
                    'email' => $user->email,
                ]
            ]
        ]);
    }

    public function login(Request $request)
{
    $data = $request->validate([
        'email' => ['required','email'],
        'password' => ['required','string'],
    ]);

    $user = User::where('email', $data['email'])->first();


    if (!$user || !Hash::check($data['password'], $user->password)) {
        return response()->json([
            'success' => false,
            'message' => 'Invalid credentials',
        ], 401);
    }

    $token = $user->createToken('api')->plainTextToken;

    return response()->json([
        'success' => true,
        'message' => 'Login success',
        'data' => [
            'token' => $token,
            'user' => [
                'id' => (string) $user->id,
                'name' => $user->name,
                'email' => $user->email,
            ]
        ]
    ]);
}

public function logout(Request $request)
{
    $request->user()->currentAccessToken()?->delete();

    return response()->json([
        'success' => true,
        'message' => 'Logged out',
        'data' => (object)[]
    ]);
}



public function refresh(Request $request)
{
    $user = $request->user();
    $currentToken = $user->currentAccessToken();
    if (!$currentToken) {
        return response()->json([
            'success' => false,
            'message' => 'Unauthorized',
            'errors' => (object)[],
        ], 401);
    }

    $currentToken->delete();
    $newToken = $user->createToken('auth_token')->plainTextToken;
    return response()->json([
        'success' => true,
        'message' => 'OK',
        'data' => [
            'token' => $newToken,
            'user' => [
                'id' => (string) $user->id,
                'name' => $user->name,
                'email' => $user->email,
                'language' => $user->language ?? 'en',
                'theme' => $user->theme ?? 'system',
            ],
        ],
    ], 200);
}


public function forgotPassword(Request $request)
{
    $request->validate([
        'email' => ['required', 'email'],
    ]);
    $email = $request->email;
    $otp = random_int(100000, 999999);
    Cache::put(
        "password_reset_otp:$email",
        Hash::make((string) $otp),
        now()->addMinutes(10)
    );
    Mail::raw(
        "Your password reset code is: $otp\nThis code is valid for 10 minutes.",
        function ($message) use ($email) {
            $message->to($email)->subject('Password Reset Code');
        }
    );

    return response()->json([
        'success' => true,
        'message' => 'OK',
        'data' => (object)[],
    ], 200);
}


public function resetPassword(Request $request)
{
    $request->validate([
        'email' => ['required', 'email'],
        'token' => ['required', 'string'], // OTP
        'password' => ['required', 'string', 'min:8', 'confirmed'],
    ]);

    $email = $request->email;
    $otp = $request->token;
    $hashedOtp = Cache::get("password_reset_otp:$email");
    if (!$hashedOtp || !Hash::check((string) $otp, $hashedOtp)) {
        return response()->json([
            'success' => false,
            'message' => 'Validation error',
            'errors' => [
                'token' => ['Invalid or expired OTP code.'],
            ],
        ], 422);
    }
    $user = User::where('email', $email)->first();
    if (!$user) {
        return response()->json([
            'success' => false,
            'message' => 'Validation error',
            'errors' => [
                'email' => ['User not found.'],
            ],
        ], 422);
    }
    $user->password = Hash::make($request->password);
    $user->save();
    Cache::forget("password_reset_otp:$email");
    return response()->json([
        'success' => true,
        'message' => 'OK',
        'data' => (object)[],
    ], 200);
}

public function me(Request $request)
{
    $user = $request->user();

    return response()->json([
        'success' => true,
        'message' => 'OK',
        'data' => [
            'id' => (string) $user->id,
            'name' => $user->name,
            'email' => $user->email,
            'language' => $user->language ?? 'en',
            'theme' => $user->theme ?? 'system',
        ],
    ], 200);
}



    public function updateProfile(Request $request)
{
    $data = $request->validate([
        'name' => ['sometimes', 'string', 'max:255'],
    ]);

    $user = $request->user();
    $user->fill($data);
    $user->save();

    return response()->json([
        'success' => true,
        'message' => 'OK',
        'data' => [
            'id' => (string) $user->id,
            'name' => $user->name,
            'email' => $user->email,
            'language' => $user->language,
            'theme' => $user->theme,
        ],
    ], 200);
}





}
