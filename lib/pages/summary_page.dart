import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:clipboard/clipboard.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';

class SummaryPage extends StatefulWidget {
  final String? fileName;

  const SummaryPage({Key? key, this.fileName}) : super(key: key);

  @override
  State<SummaryPage> createState() => _SummaryPageState();
}

class _SummaryPageState extends State<SummaryPage> {
  bool _isGenerating = false;
<<<<<<< HEAD
  String _summaryResult = "";
  final TextEditingController _textController = TextEditingController();

  // دالة لتوليد الملخص عبر FastAPI
  void _generateSummary() async {
    if (_textController.text.trim().isEmpty) return;
=======
  String? _summaryResult;
>>>>>>> flutter

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
          _summaryResult = '''This research paper explores the application of artificial intelligence in document processing and analysis. The study focuses on three key areas: automated summarization, multilingual translation, and intelligent question generation.

The findings demonstrate that AI-powered tools can significantly reduce the time required for document analysis while maintaining high accuracy rates. The paper concludes with recommendations for future development in this field.''';
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

  void _copyToClipboard() {
    if (_summaryResult != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Copied to clipboard'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
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
        backgroundColor: theme.cardColor,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
<<<<<<< HEAD
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
=======
            Container(
              width: double.infinity,
              color: theme.cardColor,
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Summary',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Icon(
                        Icons.description_outlined,
                        color: theme.iconTheme.color,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          widget.fileName ?? 'No file selected',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ],
>>>>>>> flutter
              ),
            ),
            const SizedBox(height: 16),

<<<<<<< HEAD
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
=======
            const SizedBox(height: 8),

            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: InkWell(
                  onTap: _isGenerating ? null : _generateSummary,
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: _isGenerating
                            ? [
                          Colors.grey.shade400,
                          Colors.grey.shade500,
                        ]
                            : const [
                          Color(0xFF64B5F6),
                          Color(0xFF4DD0E1),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: _isGenerating
                          ? []
                          : [
                        BoxShadow(
                          color: const Color(0xFF64B5F6).withOpacity(0.3),
                          blurRadius: 15,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_isGenerating)
                          const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation(Colors.white),
                            ),
                          )
                        else
                          const Icon(
                            Icons.summarize_rounded,
                            color: Colors.white,
                            size: 20,
                          ),
                        const SizedBox(width: 8),
                        Text(
                          _isGenerating
                              ? 'Generating Summary...'
                              : (_summaryResult == null ? 'Generate Summary' : 'Regenerate Summary'),
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
>>>>>>> flutter
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),

<<<<<<< HEAD
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
=======
            const SizedBox(height: 8),

            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Summary Result',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 20),

                  Container(
                    width: double.infinity,
                    constraints: const BoxConstraints(minHeight: 200),
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: theme.scaffoldBackgroundColor,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: theme.dividerColor),
                    ),
                    child: _isGenerating
                        ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const SizedBox(
                            width: 40,
                            height: 40,
                            child: CircularProgressIndicator(
                              strokeWidth: 3,
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Generating your summary...',
                            style: theme.textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    )
                        : (_summaryResult == null
                        ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.auto_awesome_outlined,
                            size: 50,
                            color: theme.textTheme.bodyMedium?.color?.withOpacity(0.3),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Click "Generate Summary" to start',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.textTheme.bodyMedium?.color?.withOpacity(0.5),
                            ),
                          ),
                        ],
                      ),
                    )
                        : SingleChildScrollView(
                      child: Text(
                        _summaryResult!,
                        style: theme.textTheme.bodyLarge?.copyWith(
                          height: 1.6,
                        ),
                      ),
                    )),
                  ),

                  if (_summaryResult != null) ...[
                    const SizedBox(height: 20),

                    Row(
                      children: [
                        Expanded(
                          child: InkWell(
                            onTap: _copyToClipboard,
                            borderRadius: BorderRadius.circular(12),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: theme.dividerColor),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.copy_rounded,
                                      color: theme.iconTheme.color, size: 18),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Copy',
                                    style: theme.textTheme.bodyMedium?.copyWith(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
>>>>>>> flutter
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
<<<<<<< HEAD
                          child: ElevatedButton.icon(
                            onPressed: _downloadSummary,
                            icon: const Icon(Icons.download),
                            label: const Text("Download"),
=======
                          child: InkWell(
                            onTap: () {},
                            borderRadius: BorderRadius.circular(12),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              decoration: BoxDecoration(
                                color: const Color(0xFF64B5F6).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: const Color(0xFF64B5F6),
                                ),
                              ),
                              child: const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.download_rounded,
                                      color: Color(0xFF64B5F6), size: 18),
                                  SizedBox(width: 8),
                                  Text(
                                    'Download',
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w600,
                                      color: Color(0xFF64B5F6),
                                    ),
                                  ),
                                ],
                              ),
                            ),
>>>>>>> flutter
                          ),
                        ),
                      ],
                    ),
                  ],
<<<<<<< HEAD
                ),
=======
                ],
>>>>>>> flutter
              ),
          ],
        ),
      ),
    );
  }
}