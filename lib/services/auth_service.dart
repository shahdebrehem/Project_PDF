import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class AuthService {
  final ApiService _apiService = ApiService();

  // مفاتيح منفصلة لحفظ البيانات بشكل مستقل
  static const String _avatarKey = 'user_avatar_bytes';
  static const String _createdAtKey = 'user_created_at';

  // -------------------- Authentication --------------------

  Future<Map<String, dynamic>> signUp({
    required String name,
    required String email,
    required String password,
    String? passwordConfirmation,
    Uint8List? imageBytes,
    String? imageName,
  }) async {
    try {
      FormData formData;

      if (imageBytes != null) {
        formData = FormData.fromMap({
          'name': name,
          'email': email,
          'password': password,
          'password_confirmation': passwordConfirmation ?? password,
          'image': MultipartFile.fromBytes(
            imageBytes,
            filename: imageName ?? 'profile.jpg',
            contentType: DioMediaType('image', 'jpeg'),
          ),
        });
      } else {
        formData = FormData.fromMap({
          'name': name,
          'email': email,
          'password': password,
          'password_confirmation': passwordConfirmation ?? password,
        });
      }

      final response = await _apiService.dio.post(
        '/auth/signup',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      if (response.data['success'] == true) {
        await _saveToken(response.data['data']['token']);

        Map<String, dynamic> userData = response.data['data']['user'];

        // إضافة تاريخ التسجيل
        final now = DateTime.now().toIso8601String();
        userData['createdAt'] = now;
        print('✅ Set createdAt to: $now');

        // حفظ الصورة كـ Base64
        if (imageBytes != null) {
          userData['avatarBytes'] = base64Encode(imageBytes);
          print('✅ Saved avatar as Base64, size: ${imageBytes.length} bytes');
        } else {
          print('⚠️ No avatar image provided');
        }

        print('📦 Saving new user data:');
        print('  - Name: ${userData['name']}');
        print('  - Email: ${userData['email']}');
        print('  - Has avatar: ${userData['avatarBytes'] != null}');
        print('  - CreatedAt: ${userData['createdAt']}');

        await _saveUser(userData);
        return response.data;
      }

      throw Exception(response.data['message'] ?? 'Registration failed');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiService.dio.post(
        '/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      if (response.data['success'] == true) {
        await _saveToken(response.data['data']['token']);

        Map<String, dynamic> userData = response.data['data']['user'];

        // استرجاع البيانات القديمة من التخزين المحلي
        final oldUser = await getCurrentUserFromStorage();

        if (oldUser != null) {
          // استرجاع الصورة القديمة (Base64) من المفتاح المنفصل
          final savedAvatar = await getStoredAvatar();
          if (savedAvatar != null) {
            userData['avatarBytes'] = base64Encode(savedAvatar);
            print('✅ Restored avatar from separate storage');
          } else if (oldUser['avatarBytes'] != null) {
            userData['avatarBytes'] = oldUser['avatarBytes'];
            print('✅ Restored avatar from old user data');
          }

          // استرجاع التاريخ القديم
          final savedCreatedAt = await getStoredCreatedAt();
          if (savedCreatedAt != null) {
            userData['createdAt'] = savedCreatedAt;
            print('✅ Restored createdAt from separate storage: $savedCreatedAt');
          } else if (oldUser['createdAt'] != null) {
            userData['createdAt'] = oldUser['createdAt'];
            print('✅ Restored createdAt from old user data: ${oldUser['createdAt']}');
          }
        }

        // إذا لم يكن هناك تاريخ في التخزين المحلي، استخدم تاريخ التسجيل الحالي
        if (userData['createdAt'] == null) {
          userData['createdAt'] = DateTime.now().toIso8601String();
          print('⚠️ No createdAt found, using current date');
        }

        print('📦 Saving user data:');
        print('  - Name: ${userData['name']}');
        print('  - Email: ${userData['email']}');
        print('  - Has avatar: ${userData['avatarBytes'] != null}');
        print('  - CreatedAt: ${userData['createdAt']}');

        await _saveUser(userData);
        return response.data;
      }

      throw Exception(response.data['message'] ?? 'Login failed');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> forgotPassword(String email) async {
    try {
      final response = await _apiService.dio.post(
        '/auth/forgot-password',
        data: {'email': email},
      );
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> logout() async {
    try {
      await _apiService.dio.post('/auth/logout');
    } catch (e) {
      debugPrint('Logout error: $e');
    } finally {
      // ✅ صح: بنستخدم _clearAuthData مش _clearAllData
      await _clearAuthData();
      print('✅ Logout: auth data cleared (avatar and createdAt kept)'); // غيري الرسالة دي
    }
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      final response = await _apiService.dio.get('/me');
      if (response.data['success'] == true) {
        Map<String, dynamic> userData = response.data['data'];

        // الحفاظ على الصورة والتاريخ المحلي
        final localUser = await getCurrentUserFromStorage();
        if (localUser != null) {
          if (localUser['avatarBytes'] != null) {
            userData['avatarBytes'] = localUser['avatarBytes'];
          }
          if (localUser['createdAt'] != null) {
            userData['createdAt'] = localUser['createdAt'];
          }
        }

        await _saveUser(userData);
        return response.data;
      }
      throw Exception('Failed to get user');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // -------------------- Profile Update --------------------

  Future<Map<String, dynamic>> updateProfile({
    String? name,
    Uint8List? imageBytes,
    String? imageName,
  }) async {
    try {
      FormData formData = FormData.fromMap({});

      if (name != null) {
        formData.fields.add(MapEntry('name', name));
      }

      if (imageBytes != null) {
        formData.files.add(MapEntry(
          'image',
          MultipartFile.fromBytes(
            imageBytes,
            filename: imageName ?? 'profile.jpg',
            contentType: DioMediaType('image', 'jpeg'),
          ),
        ));
      }

      final response = await _apiService.dio.put(
        '/me',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      if (response.data['success'] == true) {
        Map<String, dynamic> userData = response.data['data'];

        // الحفاظ على الصورة الجديدة كـ Base64
        if (imageBytes != null) {
          userData['avatarBytes'] = base64Encode(imageBytes);
          // تحديث الصورة في التخزين المنفصل
          await updateAvatarLocally(imageBytes);
        } else {
          // الحفاظ على الصورة القديمة إذا لم يتم تغييرها
          final localUser = await getCurrentUserFromStorage();
          if (localUser != null && localUser['avatarBytes'] != null) {
            userData['avatarBytes'] = localUser['avatarBytes'];
          }
        }

        // الحفاظ على التاريخ
        final localUser = await getCurrentUserFromStorage();
        if (localUser != null && localUser['createdAt'] != null) {
          userData['createdAt'] = localUser['createdAt'];
        }

        await _saveUser(userData);
        return response.data;
      }

      throw Exception(response.data['message'] ?? 'Update failed');
    } on DioException catch (e) {
      print('Update profile error: ${e.message}');
      print('Response status: ${e.response?.statusCode}');
      print('Response data: ${e.response?.data}');
      throw _handleError(e);
    }
  }

  // -------------------- Local Storage --------------------

  Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  Future<void> _saveUser(Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user', json.encode(user));

    // حفظ الصورة بشكل منفصل إذا وجدت
    if (user['avatarBytes'] != null) {
      await prefs.setString(_avatarKey, user['avatarBytes']);
      print('✅ Saved avatar separately');
    }

    // حفظ التاريخ بشكل منفصل
    if (user['createdAt'] != null) {
      await prefs.setString(_createdAtKey, user['createdAt']);
      print('✅ Saved createdAt separately');
    }
  }

  Future<void> _clearAuthData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user');
    // لا نمسح الصورة والتاريخ المنفصلين هنا
    print('✅ Cleared auth data (kept avatar and createdAt)');
  }

  Future<void> _clearAllData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user');
    await prefs.remove(_avatarKey);
    await prefs.remove(_createdAtKey);
    print('✅ Cleared all data including avatar');
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<Map<String, dynamic>?> getCurrentUserFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final userString = prefs.getString('user');

    if (userString != null) {
      Map<String, dynamic> userData = json.decode(userString);

      // محاولة استرجاع الصورة من المفتاح المنفصل
      final savedAvatar = prefs.getString(_avatarKey);
      if (savedAvatar != null && userData['avatarBytes'] == null) {
        userData['avatarBytes'] = savedAvatar;
        print('✅ Restored avatar from separate storage');
      }

      // محاولة استرجاع التاريخ من المفتاح المنفصل
      final savedCreatedAt = prefs.getString(_createdAtKey);
      if (savedCreatedAt != null && userData['createdAt'] == null) {
        userData['createdAt'] = savedCreatedAt;
        print('✅ Restored createdAt from separate storage');
      }

      print('📖 Reading user from storage:');
      print('  - Name: ${userData['name']}');
      print('  - Has avatarBytes: ${userData['avatarBytes'] != null}');
      print('  - CreatedAt: ${userData['createdAt']}');

      return userData;
    }
    print('⚠️ No user found in storage');
    return null;
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }

  // دالة مساعدة للحصول على صورة المستخدم كـ Uint8List
  Uint8List? getUserAvatarBytes(Map<String, dynamic>? user) {
    if (user == null) return null;

    if (user['avatarBytes'] != null) {
      try {
        return base64Decode(user['avatarBytes']);
      } catch (e) {
        return null;
      }
    }

    return null;
  }

  // دالة مساعدة لتحديث الصورة فقط في التخزين المنفصل
  Future<void> updateAvatarLocally(Uint8List? imageBytes) async {
    final prefs = await SharedPreferences.getInstance();

    if (imageBytes != null) {
      final avatarBase64 = base64Encode(imageBytes);
      await prefs.setString(_avatarKey, avatarBase64);

      // تحديث الصورة في كائن المستخدم أيضاً
      final user = await getCurrentUserFromStorage();
      if (user != null) {
        user['avatarBytes'] = avatarBase64;
        await _saveUser(user);
      }
      print('✅ Updated avatar locally');
    } else {
      await prefs.remove(_avatarKey);
      print('✅ Removed avatar locally');
    }
  }

  // دالة مساعدة للحصول على الصورة المحفوظة
  Future<Uint8List?> getStoredAvatar() async {
    final prefs = await SharedPreferences.getInstance();
    final avatarString = prefs.getString(_avatarKey);

    if (avatarString != null) {
      try {
        return base64Decode(avatarString);
      } catch (e) {
        print('Error decoding avatar: $e');
        return null;
      }
    }
    return null;
  }

  // دالة مساعدة للحصول على التاريخ المحفوظ
  Future<String?> getStoredCreatedAt() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_createdAtKey);
  }

  // دالة مساعدة لحفظ التاريخ بشكل منفصل
  Future<void> updateCreatedAtLocally(String createdAt) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_createdAtKey, createdAt);
    print('✅ Updated createdAt locally: $createdAt');
  }

  // أضف هذه الدالة في AuthService
  Future<Uint8List?> getCurrentUserAvatar() async {
    final prefs = await SharedPreferences.getInstance();
    final avatarString = prefs.getString(_avatarKey);

    if (avatarString != null) {
      try {
        return base64Decode(avatarString);
      } catch (e) {
        print('Error decoding avatar: $e');
        return null;
      }
    }
    return null;
  }

// أضف دالة للحصول على بيانات المستخدم كاملة مع الصورة
  Future<Map<String, dynamic>?> getCurrentUserWithAvatar() async {
    final user = await getCurrentUserFromStorage();
    if (user != null) {
      final avatar = await getCurrentUserAvatar();
      if (avatar != null) {
        user['avatarBytes'] = base64Encode(avatar);
      }
    }
    return user;
  }

  // -------------------- Error Handling --------------------

  String _handleError(DioException e) {
    if (e.response != null) {
      final data = e.response?.data;
      if (data is Map) {
        if (data['success'] == false) {
          if (data['message'] != null) {
            return data['message'];
          }
          if (data['errors'] != null) {
            final errors = data['errors'] as Map;
            if (errors.isNotEmpty) {
              final firstError = errors.values.first;
              if (firstError is List && firstError.isNotEmpty) {
                return firstError[0];
              }
            }
          }
        }
        if (data['message'] != null) {
          return data['message'];
        }
      }
      return 'Server error: ${e.response?.statusCode}';
    } else if (e.type == DioExceptionType.connectionTimeout) {
      return 'Connection timeout - check your internet';
    } else if (e.type == DioExceptionType.receiveTimeout) {
      return 'Server is not responding';
    } else if (e.type == DioExceptionType.cancel) {
      return 'Request cancelled';
    } else if (e.type == DioExceptionType.connectionError) {
      return 'No internet connection';
    } else {
      return 'Network error: ${e.message}';
    }
  }
}