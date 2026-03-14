import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class AuthService {
  final ApiService _apiService = ApiService();

  // -------------------- Authentication --------------------

  Future<Map<String, dynamic>> signUp({
    required String name,
    required String email,
    required String password,
    String? passwordConfirmation,
    File? image, // إضافة صورة المستخدم
  }) async {
    try {
      FormData formData;

      if (image != null) {
        // لو في صورة، نستخدم FormData
        formData = FormData.fromMap({
          'name': name,
          'email': email,
          'password': password,
          'password_confirmation': passwordConfirmation ?? password,
          'image': await MultipartFile.fromFile(image.path, filename: 'profile.jpg'),
        });
      } else {
        // لو مفيش صورة، نستخدم JSON عادي
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
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        ),
      );

      if (response.data['success'] == true) {
        await _saveToken(response.data['data']['token']);
        await _saveUser(response.data['data']['user']);
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
        await _saveUser(response.data['data']['user']);
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
      await _clearAuthData();
    }
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      final response = await _apiService.dio.get('/me');
      if (response.data['success'] == true) {
        await _saveUser(response.data['data']);
        return response.data;
      }
      throw Exception('Failed to get user');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // -------------------- Profile Update with Image --------------------

  Future<Map<String, dynamic>> updateProfile({
    String? name,
    File? image,
  }) async {
    try {
      FormData formData = FormData.fromMap({});

      if (name != null) {
        formData.fields.add(MapEntry('name', name));
      }

      if (image != null) {
        formData.files.add(MapEntry(
          'image',
          await MultipartFile.fromFile(image.path, filename: 'profile.jpg'),
        ));
      }

      final response = await _apiService.dio.post(
        '/me/update',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      if (response.data['success'] == true) {
        await _saveUser(response.data['data']);
        return response.data;
      }

      throw Exception(response.data['message'] ?? 'Update failed');
    } on DioException catch (e) {
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
  }

  Future<void> _clearAuthData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user');
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<Map<String, dynamic>?> getCurrentUserFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final userString = prefs.getString('user');
    if (userString != null) {
      return json.decode(userString);
    }
    return null;
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
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