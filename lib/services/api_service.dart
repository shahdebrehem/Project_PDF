// services/api_service.dart
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  ApiService._internal() {
    _init();
  }

  late Dio dio;

  // حددي البيئة المناسبة
  static const String baseUrl = 'http://10.0.2.2:8000/api'; // للـ Emulator
  // static const String baseUrl = 'http://localhost:8000/api'; // للـ iOS Simulator
  // static const String baseUrl = 'http://192.168.1.x:8000/api'; // للجهاز الحقيقي

  bool _initialized = false;

  void _init() {
    if (_initialized) return;
    _initialized = true;

    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        print('🌐 Request: ${options.method} ${options.path}');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        print('✅ Response: ${response.statusCode}');
        return handler.next(response);
      },
      onError: (DioException e, handler) {
        print('❌ Error: ${e.message}');
        return handler.next(e);
      },
    ));
  }
}