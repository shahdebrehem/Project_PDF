// services/files_service.dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'api_service.dart';

class FilesService {
  final ApiService _apiService = ApiService();

  Future<List<Map<String, dynamic>>> getRecentFiles() async {
    try {
      final response = await _apiService.dio.get('/files/recent');

      if (response.data['success'] == true) {
        final List list = response.data['data'] ?? [];
        return list.map((e) => Map<String, dynamic>.from(e)).toList();
      }
      return [];
    } catch (e) {
      print('Error getting files: $e');
      return [];
    }
  }

  // ✅ دالة اختيار ورفع الملف
  Future<Map<String, dynamic>?> pickAndUploadFile() async {
    try {
      // اختيار الملف
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        allowMultiple: false,
      );

      if (result == null) {
        return null; // المستخدم ألغى الاختيار
      }

      // الحصول على مسار الملف
      String? filePath = result.files.single.path;
      if (filePath == null) return null;

      File file = File(filePath);
      String fileName = result.files.single.name;

      // إنشاء FormData للرفع
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(file.path, filename: fileName),
        'type': 'PDF',
      });

      // رفع الملف
      final response = await _apiService.dio.post(
        '/files/upload',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      if (response.data['success'] == true) {
        return response.data['data'];
      }
      return null;
    } catch (e) {
      print('Error uploading file: $e');
      return null;
    }
  }

  // ✅ دالة رفع ملف بمسار محدد (اختياري)
  Future<Map<String, dynamic>?> uploadFile(File file, {String type = 'Summary'}) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(file.path),
        'type': type,
      });

      final response = await _apiService.dio.post(
        '/files/upload',
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );

      if (response.data['success'] == true) {
        return response.data['data'];
      }
      return null;
    } catch (e) {
      print('Error uploading file: $e');
      return null;
    }
  }

  Future<bool> deleteFile(String fileId) async {
    try {
      final response = await _apiService.dio.delete('/files/$fileId');
      return response.data['success'] == true;
    } catch (e) {
      print('Error deleting file: $e');
      return false;
    }
  }
}