import 'dart:convert';
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
  }) async {
    try {
      final response = await _apiService.dio.post(
        '/auth/signup',
        data: {
          'name': name,
          'email': email,
          'password': password,
          'password_confirmation': passwordConfirmation ?? password,
        },
      );

      if (response.data['token'] != null) {
        await _saveToken(response.data['token']);
        await _saveUser(response.data['user']);
      }

      return response.data;
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

      // Save token and user data
      if (response.data['token'] != null) {
        await _saveToken(response.data['token']);
        await _saveUser(response.data['user']);
      }

      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> logout() async {
    try {
      await _apiService.dio.post('/auth/logout');
    } on DioException catch (e) {
      debugPrint('Logout error: $e');
    } finally {
      // Clear local storage even if API call fails
      await _clearAuthData();
    }
  }

  Future<Map<String, dynamic>> refreshToken() async {
    try {
      final response = await _apiService.dio.post('/auth/refresh');
      if (response.data['token'] != null) {
        await _saveToken(response.data['token']);
      }
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // -------------------- User Profile --------------------

  Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      final response = await _apiService.dio.get('/me');
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> updateProfile({
    String? name,
    String? email,
    String? phone,
  }) async {
    try {
      final response = await _apiService.dio.put(
        '/me',
        data: {
          if (name != null) 'name': name,
          if (email != null) 'email': email,
          if (phone != null) 'phone': phone,
        },
      );

      if (response.data['user'] != null) {
        await _saveUser(response.data['user']);
      }

      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // -------------------- Password Management --------------------

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

  Future<Map<String, dynamic>> resetPassword({
    required String email,
    required String token,
    required String password,
    required String passwordConfirmation,
  }) async {
    try {
      final response = await _apiService.dio.post(
        '/auth/reset-password',
        data: {
          'email': email,
          'token': token,
          'password': password,
          'password_confirmation': passwordConfirmation,
        },
      );
      return response.data;
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
      // Server responded with error
      final data = e.response?.data;
      if (data is Map) {
        if (data['message'] != null) {
          return data['message'];
        }
        if (data['errors'] != null) {
          final errors = data['errors'] as Map;
          return errors.values.first[0];
        }
      }
      return 'Server error occurred'; // ✅
    } else if (e.type == DioExceptionType.connectionTimeout) {
      return 'Connection timeout'; // ✅
    } else if (e.type == DioExceptionType.receiveTimeout) {
      return 'Receive timeout'; // ✅
    } else if (e.type == DioExceptionType.cancel) {
      return 'Request cancelled'; // ✅
    } else {
      return 'Network error - check your connection'; // ✅
    }
  }}