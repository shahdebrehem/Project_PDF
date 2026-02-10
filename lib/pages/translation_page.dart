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
    },
    {
      'value': 'arabic_english',
      'label': 'Arabic → English',
    },
    {
      'value': 'english_french',
      'label': 'English → French',
    },
  ];

  void _translateDocument() {
    setState(() {
      _isTranslating = true;
    });

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isTranslating = false;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Translation'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              width: double.infinity,
              color: theme.cardColor,
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Translation',
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
                      Text(
                        'Research_Paper_2024.pdf',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Language Selection
            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Select Language',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 20),
                  ..._languageOptions.map(
                        (option) => _buildLanguageOption(
                      theme: theme,
                      value: option['value'],
                      label: option['label'],
                      isSelected: _selectedLanguage == option['value'],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Translate Button
            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: InkWell(
                  onTap: _isTranslating ? null : _translateDocument,
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: _isTranslating
                            ? [
                          theme.disabledColor,
                          theme.disabledColor.withOpacity(0.8),
                        ]
                            : const [
                          Color(0xFF64B5F6),
                          Color(0xFF4DD0E1),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_isTranslating)
                          const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor:
                              AlwaysStoppedAnimation(Colors.white),
                            ),
                          )
                        else
                          const Icon(
                            Icons.translate_rounded,
                            color: Colors.white,
                            size: 20,
                          ),
                        const SizedBox(width: 8),
                        Text(
                          _isTranslating ? 'Translating...' : 'Translate',
                          style: const TextStyle(
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

            const SizedBox(height: 8),

            // Result Section
            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Translation Result',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Container(
                    width: double.infinity,
                    constraints: const BoxConstraints(minHeight: 200),
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: theme.scaffoldBackgroundColor,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: theme.dividerColor),
                    ),
                    child: _isTranslating
                        ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const CircularProgressIndicator(),
                          const SizedBox(height: 16),
                          Text(
                            'Translating your document...',
                            style: theme.textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    )
                        : Text(
                      _buildSampleTranslation(),
                      style: theme.textTheme.bodyLarge?.copyWith(
                        height: 1.6,
                      ),
                      textDirection: _getTextDirection(),
                    ),
                  ),
                  const SizedBox(height: 20),
                  InkWell(
                    onTap: () {},
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: theme.dividerColor),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.download_rounded,
                              color: theme.iconTheme.color),
                          const SizedBox(width: 8),
                          Text(
                            'Download Translation',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
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
    required ThemeData theme,
    required String value,
    required String label,
    required bool isSelected,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isSelected
            ? const Color(0xFF64B5F6).withOpacity(0.1)
            : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isSelected
              ? const Color(0xFF64B5F6)
              : theme.dividerColor,
          width: isSelected ? 2 : 1,
        ),
      ),
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
              Icon(
                Icons.radio_button_checked,
                color: isSelected
                    ? const Color(0xFF64B5F6)
                    : theme.disabledColor,
              ),
              const SizedBox(width: 16),
              Text(
                label,
                style: theme.textTheme.bodyLarge?.copyWith(
                  fontWeight:
                  isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected
                      ? const Color(0xFF64B5F6)
                      : theme.textTheme.bodyLarge?.color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _buildSampleTranslation() {
    switch (_selectedLanguage) {
      case 'english_arabic':
        return 'هذا ترجمة نموذجية للمستند. هذا النص يظهر كيف سيبدو المحتوى المترجم.';
      case 'arabic_english':
        return 'This is a sample translation of the document.';
      case 'english_french':
        return 'Ceci est un exemple de traduction du document.';
      default:
        return '';
    }
  }

  TextDirection _getTextDirection() {
    return _selectedLanguage == 'english_arabic'
        ? TextDirection.rtl
        : TextDirection.ltr;
  }
}
