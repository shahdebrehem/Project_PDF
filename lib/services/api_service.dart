// services/api_service.dart
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

// api_service.dart - لا يحتاج تعديل كبير، لكن تأكد من الـ baseUrl
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  ApiService._internal() {
    _init();
  }

  late Dio dio;

  // ✅ تأكد من أن هذا الـ IP صحيح (عنوان جهاز السيرفر)
  static const String baseUrl = 'http://192.168.1.176:8000/api';

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
          print('🔑 Token added to request: ${options.method} ${options.path}');
        } else {
          print('⚠️ No token found for request: ${options.method} ${options.path}');
        }
        print('🌐 Request: ${options.method} ${options.path}');
        print('📦 Headers: ${options.headers}');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        print('✅ Response: ${response.statusCode} - ${response.requestOptions.path}');
        return handler.next(response);
      },
      onError: (DioException e, handler) {
        print('❌ Error: ${e.message}');
        print('Status: ${e.response?.statusCode}');
        print('URL: ${e.requestOptions.path}');
        print('Response data: ${e.response?.data}');
        return handler.next(e);
      },
    ));
  }
}