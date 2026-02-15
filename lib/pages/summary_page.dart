// pages/summary_page.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:clipboard/clipboard.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';

class SummaryPage extends StatefulWidget {
  const SummaryPage({Key? key}) : super(key: key);

  @override
  State<SummaryPage> createState() => _SummaryPageState();
}

class _SummaryPageState extends State<SummaryPage> {
  bool _isGenerating = false;
  String _summaryResult = "";
  final TextEditingController _textController = TextEditingController();

  // دالة لتوليد الملخص عبر FastAPI
  void _generateSummary() async {
    if (_textController.text.trim().isEmpty) return;

    setState(() {
      _isGenerating = true;
      _summaryResult = "";
    });

    try {
      final url = Uri.parse('http://127.0.0.1:8000/summarize'); // لو Flutter Emulator استخدم 10.0.2.2
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"text": _textController.text}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _summaryResult = data['summary'] ?? "No summary generated";
        });
      } else {
        setState(() {
          _summaryResult = "Error: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _summaryResult = "Error: $e";
      });
    } finally {
      if (mounted) {
        setState(() {
          _isGenerating = false;
        });
      }
    }
  }

  // نسخ النص
  void _copySummary() {
    if (_summaryResult.isNotEmpty) {
      FlutterClipboard.copy(_summaryResult).then((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Summary copied!")),
        );
      });
    }
  }

  // تحميل النص كملف
  void _downloadSummary() async {
    if (_summaryResult.isNotEmpty) {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/summary.txt');
      await file.writeAsString(_summaryResult);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Summary saved to ${file.path}")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Summary'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // إدخال النص
            TextField(
              controller: _textController,
              minLines: 5,
              maxLines: 10,
              decoration: InputDecoration(
                hintText: "Paste your text here...",
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // زر توليد الملخص
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isGenerating ? null : _generateSummary,
                icon: _isGenerating
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Icon(Icons.summarize),
                label: Text(
                  _isGenerating ? "Generating..." : "Generate Summary",
                  style: const TextStyle(fontSize: 16),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // صندوق النتيجة
            if (_summaryResult.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: theme.cardColor,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: theme.dividerColor),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Summary Result',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _summaryResult,
                      style: theme.textTheme.bodyMedium?.copyWith(height: 1.5),
                    ),
                    const SizedBox(height: 16),

                    // أزرار Copy و Download
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: _copySummary,
                            icon: const Icon(Icons.copy),
                            label: const Text("Copy"),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: _downloadSummary,
                            icon: const Icon(Icons.download),
                            label: const Text("Download"),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
