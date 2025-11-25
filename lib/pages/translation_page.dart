// pages/translation_page.dart
import 'package:flutter/material.dart';

class TranslationPage extends StatefulWidget {
  const TranslationPage({Key? key}) : super(key: key);

  @override
  State<TranslationPage> createState() => _TranslationPageState();
}

class _TranslationPageState extends State<TranslationPage> {
  String? _selectedLanguage = 'english_arabic';
  bool _isTranslating = false;

  final List<Map<String, dynamic>> _languageOptions = [
    {
      'value': 'english_arabic',
      'label': 'English → Arabic',
      'from': 'English',
      'to': 'Arabic'
    },
    {
      'value': 'arabic_english',
      'label': 'Arabic → English',
      'from': 'Arabic',
      'to': 'English'
    },
    {
      'value': 'english_french',
      'label': 'English → French',
      'from': 'English',
      'to': 'French'
    },
  ];

  void _translateDocument() {
    setState(() {
      _isTranslating = true;
    });

    // محاكاة عملية الترجمة
    Future.delayed(Duration(seconds: 2), () {
      setState(() {
        _isTranslating = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('Translation'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.black87),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Section
            Container(
              width: double.infinity,
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Translation',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Icon(Icons.description_outlined, color: Colors.grey.shade600, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Research_Paper_2024.pdf',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey.shade600,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Language Selection Section
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Select Language',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Language Options
                  ..._languageOptions.map((option) => _buildLanguageOption(
                    value: option['value'],
                    label: option['label'],
                    isSelected: _selectedLanguage == option['value'],
                  )),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Translate Button Section
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: _isTranslating ? null : _translateDocument,
                    borderRadius: BorderRadius.circular(16),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: _isTranslating
                              ? [Colors.grey.shade400, Colors.grey.shade500]
                              : [Color(0xFF64B5F6), Color(0xFF4DD0E1)],
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: _isTranslating
                            ? []
                            : [
                          BoxShadow(
                            color: Color(0xFF64B5F6).withOpacity(0.3),
                            blurRadius: 15,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (_isTranslating)
                            SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation(Colors.white),
                              ),
                            )
                          else
                            Icon(
                              Icons.translate_rounded,
                              color: Colors.white,
                              size: 20,
                            ),
                          const SizedBox(width: 8),
                          Text(
                            _isTranslating ? 'Translating...' : 'Translate',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 8),

            // Translation Result Section
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Translation Result',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Result Box
                  Container(
                    width: double.infinity,
                    constraints: BoxConstraints(minHeight: 200),
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: _isTranslating
                        ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 40,
                            height: 40,
                            child: CircularProgressIndicator(
                              strokeWidth: 3,
                              valueColor: AlwaysStoppedAnimation(Color(0xFF64B5F6)),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Translating your document...',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    )
                        : SingleChildScrollView(
                      child: Text(
                        _buildSampleTranslation(),
                        style: TextStyle(
                          fontSize: 16,
                          height: 1.6,
                          color: Colors.black87,
                        ),
                        textDirection: _getTextDirection(),
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Download Button
                  SizedBox(
                    width: double.infinity,
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: () {},
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          decoration: BoxDecoration(
                            color: Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.download_rounded,
                                color: Colors.grey.shade700,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Download Translation',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                  color: Colors.grey.shade700,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageOption({
    required String value,
    required String label,
    required bool isSelected,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isSelected ? Color(0xFF64B5F6).withOpacity(0.1) : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isSelected ? Color(0xFF64B5F6) : Colors.grey.shade300,
          width: isSelected ? 2 : 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            setState(() {
              _selectedLanguage = value;
            });
          },
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 20,
                  height: 20,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: isSelected ? Color(0xFF64B5F6) : Colors.grey.shade400,
                      width: 2,
                    ),
                  ),
                  child: isSelected
                      ? Container(
                    margin: EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Color(0xFF64B5F6),
                    ),
                  )
                      : null,
                ),
                const SizedBox(width: 16),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                    color: isSelected ? Color(0xFF64B5F6) : Colors.black87,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _buildSampleTranslation() {
    switch (_selectedLanguage) {
      case 'english_arabic':
        return 'هذا ترجمة نموذجية للمستند. هذا النص يظهر كيف سيبدو المحتوى المترجم. يمكنك رؤية النتائج هنا باللغة العربية.';
      case 'arabic_english':
        return 'This is a sample translation of the document. This text shows how the translated content will appear. You can see the results here in English.';
      case 'english_french':
        return 'Ceci est un exemple de traduction du document. Ce texte montre comment le contenu traduit apparaîtra. Vous pouvez voir les résultats ici en français.';
      default:
        return 'Select a language to see translation results.';
    }
  }

  TextDirection _getTextDirection() {
    if (_selectedLanguage == 'english_arabic') {
      return TextDirection.rtl;
    }
    return TextDirection.ltr;
  }
}