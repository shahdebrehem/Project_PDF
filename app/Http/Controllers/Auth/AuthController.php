<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Storage;

class AuthController extends Controller
{
    public function signup(Request $request)
    {
        try {
            $data = $request->validate([
                'name' => ['required', 'string', 'max:255'],
                'email' => ['required', 'email', 'max:255', 'unique:users,email'],
                'password' => ['required', 'string', 'min:8', 'confirmed'],
                'image' => ['nullable', 'image', 'mimes:jpeg,png,jpg', 'max:2048'], // ✅ إضافة الصورة
            ]);

            $userData = [
                'name' => $data['name'],
                'email' => $data['email'],
                'password' => Hash::make($data['password']),
                'created_at' => now(), // ✅ إضافة تاريخ الإنشاء
                'updated_at' => now(),
            ];

            // ✅ تخزين الصورة إذا وجدت
            if ($request->hasFile('image')) {
                $image = $request->file('image');
                $imageName = time() . '_' . $image->getClientOriginalName();
                
                // تخزين الصورة في مجلد public/uploads/avatars
                $image->move(public_path('uploads/avatars'), $imageName);
                $userData['avatar'] = url('uploads/avatars/' . $imageName); // ✅ حفظ URL الكامل
            }

            $user = User::create($userData);
            $token = auth()->login($user);

            return response()->json([
                'success' => true,
                'message' => 'Registered successfully',
                'data' => [
                    'token' => $token,
                    'user' => [
                        'id' => (string) $user->id,
                        'name' => $user->name,
                        'email' => $user->email,
                        'avatar' => $user->avatar ?? null, // ✅ إرجاع الصورة
                        'created_at' => $user->created_at, // ✅ إرجاع التاريخ
                    ]
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function login(Request $request)
    {
        try {
            $data = $request->validate([
                'email' => ['required', 'email'],
                'password' => ['required', 'string'],
            ]);

            $user = User::where('email', $data['email'])->first();

            if (!$user || !Hash::check($data['password'], $user->password)) {
                return response()->json([
                    'success' => false,
                    'message' => 'Invalid credentials',
                ], 401);
            }

            $token = auth()->login($user);

            return response()->json([
                'success' => true,
                'message' => 'Login success',
                'data' => [
                    'token' => $token,
                    'user' => [
                        'id' => (string) $user->id,
                        'name' => $user->name,
                        'email' => $user->email,
                        'avatar' => $user->avatar ?? null, // ✅ إرجاع الصورة
                        'created_at' => $user->created_at, // ✅ إرجاع التاريخ
                        'language' => $user->language ?? 'en',
                        'theme' => $user->theme ?? 'system',
                    ]
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function logout(Request $request)
    {
        auth()->logout();
        
        return response()->json([
            'success' => true,
            'message' => 'Logged out',
            'data' => (object)[]
        ]);
    }

    public function refresh(Request $request)
    {
        if (!auth()->check()) {
            return response()->json([
                'success' => false,
                'message' => 'Unauthorized'
            ], 401);
        }

        $user = $request->user();
        $token = auth()->refresh();

        return response()->json([
            'success' => true,
            'message' => 'OK',
            'data' => [
                'token' => $token,
                'user' => [
                    'id' => (string) $user->id,
                    'name' => $user->name,
                    'email' => $user->email,
                    'avatar' => $user->avatar ?? null, // ✅ إرجاع الصورة
                    'created_at' => $user->created_at, // ✅ إرجاع التاريخ
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

        if (!User::where('email', $email)->exists()) {
            return response()->json([
                'success' => false,
                'message' => 'User not found'
            ], 404);
        }
        
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
            'token' => ['required', 'string'],
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
                'avatar' => $user->avatar ?? null, // ✅ إرجاع الصورة
                'created_at' => $user->created_at, // ✅ إرجاع التاريخ
                'language' => $user->language ?? 'en',
                'theme' => $user->theme ?? 'system',
            ],
        ], 200);
    }

    public function updateProfile(Request $request)
    {
        try {
            $data = $request->validate([
                'name' => ['sometimes', 'string', 'max:255'],
                'image' => ['nullable', 'image', 'mimes:jpeg,png,jpg', 'max:2048'], // ✅ إضافة الصورة
            ]);

            $user = $request->user();

            // ✅ تحديث الاسم إذا وجد
            if ($request->has('name')) {
                $user->name = $request->name;
            }

            // ✅ تحديث الصورة إذا وجدت
            if ($request->hasFile('image')) {
                // حذف الصورة القديمة إذا كانت موجودة
                if ($user->avatar && file_exists(public_path(str_replace(url('/'), '', $user->avatar)))) {
                    $oldImagePath = public_path(str_replace(url('/'), '', $user->avatar));
                    if (file_exists($oldImagePath)) {
                        unlink($oldImagePath);
                    }
                }
                
                $image = $request->file('image');
                $imageName = time() . '_' . $image->getClientOriginalName();
                $image->move(public_path('uploads/avatars'), $imageName);
                $user->avatar = url('uploads/avatars/' . $imageName);
            }

            $user->updated_at = now();
            $user->save();

            return response()->json([
                'success' => true,
                'message' => 'Profile updated successfully',
                'data' => [
                    'id' => (string) $user->id,
                    'name' => $user->name,
                    'email' => $user->email,
                    'avatar' => $user->avatar ?? null, // ✅ إرجاع الصورة المحدثة
                    'created_at' => $user->created_at, // ✅ إرجاع التاريخ
                    'language' => $user->language ?? 'en',
                    'theme' => $user->theme ?? 'system',
                ],
            ], 200);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage()
            ], 500);
        }
    }
}