// services/files_service.dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'api_service.dart';

class FilesService {
  final ApiService _apiService = ApiService();

  Future<List<Map<String, dynamic>>> getRecentFiles() async {
    final response = await _apiService.dio.get('/files/recent');
    final List list = response.data['data'];
    return list.map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<void> uploadFile(File file) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path),
    });

    await _apiService.dio.post('/files/upload', data: formData);
  }
}
