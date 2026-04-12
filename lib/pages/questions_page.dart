import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';

class QuestionsPage extends StatefulWidget {
  final String? fileName;

  const QuestionsPage({Key? key, this.fileName}) : super(key: key);

  @override
  State<QuestionsPage> createState() => _QuestionsPageState();
}

class _QuestionsPageState extends State<QuestionsPage>
    with SingleTickerProviderStateMixin {
  String _selectedQuestionType = 'multiple';
  String _selectedDifficulty = 'medium';
  bool _isGenerating = false;
  late String _currentLanguage;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  final List<Map<String, dynamic>> _questionTypes = [
    {'value': 'multiple', 'label': 'multipleChoice', 'icon': Icons.quiz_rounded},
    {'value': 'truefalse', 'label': 'trueFalse', 'icon': Icons.check_circle_outline_rounded},
    {'value': 'short', 'label': 'shortAnswer', 'icon': Icons.edit_note_rounded},
  ];

  final List<Map<String, dynamic>> _difficulties = [
    {'value': 'easy', 'label': 'easy', 'color': Color(0xFF10B981)},
    {'value': 'medium', 'label': 'medium', 'color': Color(0xFFF59E0B)},
    {'value': 'hard', 'label': 'hard', 'color': Color(0xFFEF4444)},
  ];

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeOut),
    );

    _slideAnimation = Tween<Offset>(begin: const Offset(0, 0.2), end: Offset.zero).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeOutCubic),
    );

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _currentLanguage = Localizations.localeOf(context).languageCode;
  }

  bool get isArabic => _currentLanguage == 'ar';

  void _generateQuestions() {
    setState(() {
      _isGenerating = true;
    });

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isGenerating = false;
        });

        // Show success snackbar after generation
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.white, size: 20),
                const SizedBox(width: 12),
                Expanded(child: Text(isArabic ? 'تم إنشاء الأسئلة بنجاح' : 'Questions generated successfully')),
              ],
            ),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final loc = AppLocalizations.of(context)!;

    return Directionality(
      textDirection: isArabic ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        backgroundColor: theme.scaffoldBackgroundColor,
        appBar: AppBar(
          title: Text(
            loc.questionsGeneratorTitle,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          elevation: 0,
          backgroundColor: theme.cardColor,
        ),
        body: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          child: Column(
            children: [
              // Header Section
              FadeTransition(
                opacity: _fadeAnimation,
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: theme.cardColor,
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(32),
                      bottomRight: Radius.circular(32),
                    ),
                  ),
                  padding: const EdgeInsets.fromLTRB(24, 32, 24, 32),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        loc.questionsGeneratorTitle,
                        style: theme.textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        isArabic
                            ? 'أنشئ أسئلة ذكية من مستنداتك'
                            : 'Generate smart questions from your documents',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              const Color(0xFF6366F1).withOpacity(0.1),
                              const Color(0xFF8B5CF6).withOpacity(0.05),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: const Color(0xFF6366F1).withOpacity(0.2),
                          ),
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: const Color(0xFF6366F1).withOpacity(0.2),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Icon(
                                Icons.description_rounded,
                                color: const Color(0xFF6366F1),
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                widget.fileName ?? (isArabic ? 'لم يتم اختيار ملف' : 'No file selected'),
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  fontWeight: FontWeight.w500,
                                  letterSpacing: -0.3,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 12),

              // Configuration Section
              SlideTransition(
                position: _slideAnimation,
                child: Container(
                  decoration: BoxDecoration(
                    color: theme.cardColor,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                              ),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.tune_rounded,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text(
                            loc.configuration,
                            style: theme.textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              letterSpacing: -0.5,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Question Type
                      Text(
                        loc.questionType,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: _questionTypes.map((type) => _buildOptionChip(
                          theme: theme,
                          label: locByKey(loc, type['label']),
                          value: type['value'],
                          groupValue: _selectedQuestionType,
                          icon: type['icon'] as IconData,
                          onSelected: (value) {
                            setState(() {
                              _selectedQuestionType = value;
                            });
                          },
                        )).toList(),
                      ),

                      const SizedBox(height: 28),

                      // Difficulty Level
                      Text(
                        loc.difficultyLevel,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: _difficulties.map((difficulty) => _buildDifficultyChip(
                          theme: theme,
                          label: locByKey(loc, difficulty['label']),
                          value: difficulty['value'],
                          groupValue: _selectedDifficulty,
                          color: difficulty['color'] as Color,
                          onSelected: (value) {
                            setState(() {
                              _selectedDifficulty = value;
                            });
                          },
                        )).toList(),
                      ),

                      const SizedBox(height: 32),

                      // Generate Button
                      TweenAnimationBuilder(
                        tween: Tween<double>(begin: 0, end: 1),
                        duration: const Duration(milliseconds: 600),
                        builder: (context, double value, child) {
                          return Transform.scale(
                            scale: value,
                            child: SizedBox(
                              width: double.infinity,
                              child: GestureDetector(
                                onTap: _isGenerating ? null : _generateQuestions,
                                child: AnimatedContainer(
                                  duration: const Duration(milliseconds: 300),
                                  padding: const EdgeInsets.symmetric(vertical: 16),
                                  decoration: BoxDecoration(
                                    gradient: _isGenerating
                                        ? LinearGradient(
                                      colors: [Colors.grey.shade400, Colors.grey.shade500],
                                    )
                                        : const LinearGradient(
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                      colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                                    ),
                                    borderRadius: BorderRadius.circular(20),
                                    boxShadow: _isGenerating
                                        ? []
                                        : [
                                      BoxShadow(
                                        color: const Color(0xFF6366F1).withOpacity(0.4),
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
                                          width: 22,
                                          height: 22,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2.5,
                                            valueColor: AlwaysStoppedAnimation(Colors.white),
                                          ),
                                        )
                                      else
                                        const Icon(
                                          Icons.auto_awesome_rounded,
                                          color: Colors.white,
                                          size: 22,
                                        ),
                                      const SizedBox(width: 10),
                                      Text(
                                        _isGenerating
                                            ? loc.generatingQuestions
                                            : loc.generateQuestions,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w600,
                                          color: Colors.white,
                                          letterSpacing: -0.3,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 12),

              // Questions Result Section
              SlideTransition(
                position: Tween<Offset>(
                  begin: const Offset(0, 0.3),
                  end: Offset.zero,
                ).animate(CurvedAnimation(
                  parent: _animationController,
                  curve: Curves.easeOutCubic,
                )),
                child: Container(
                  decoration: BoxDecoration(
                    color: theme.cardColor,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFFF59E0B), Color(0xFFFBBF24)],
                              ),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.quiz_rounded,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text(
                            loc.generatedQuestions,
                            style: theme.textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              letterSpacing: -0.5,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        loc.questionsBasedOnContent,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      const SizedBox(height: 24),

                      ..._getSampleQuestions(loc).asMap().entries.map((entry) {
                        int index = entry.key;
                        Map<String, String> question = entry.value;
                        return SlideTransition(
                          position: Tween<Offset>(
                            begin: const Offset(0.2, 0),
                            end: Offset.zero,
                          ).animate(CurvedAnimation(
                            parent: _animationController,
                            curve: Interval(0.2 + (index * 0.05), 1.0, curve: Curves.easeOutCubic),
                          )),
                          child: QuestionItem(
                            theme: theme,
                            question: question['question']!,
                            answer: question['answer']!,
                            type: question['type']!,
                            difficulty: question['difficulty']!,
                            loc: loc,
                          ),
                        );
                      }).toList(),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOptionChip({
    required ThemeData theme,
    required String label,
    required String value,
    required String groupValue,
    required IconData icon,
    required Function(String) onSelected,
  }) {
    bool isSelected = groupValue == value;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => onSelected(value),
        borderRadius: BorderRadius.circular(30),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            color: isSelected
                ? const Color(0xFF6366F1).withOpacity(0.1)
                : theme.dividerColor.withOpacity(0.05),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(
              color: isSelected ? const Color(0xFF6366F1) : theme.dividerColor,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 18,
                color: isSelected ? const Color(0xFF6366F1) : theme.textTheme.bodyLarge?.color,
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: isSelected ? const Color(0xFF6366F1) : theme.textTheme.bodyLarge?.color,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDifficultyChip({
    required ThemeData theme,
    required String label,
    required String value,
    required String groupValue,
    required Color color,
    required Function(String) onSelected,
  }) {
    bool isSelected = groupValue == value;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => onSelected(value),
        borderRadius: BorderRadius.circular(30),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? color.withOpacity(0.1) : theme.dividerColor.withOpacity(0.05),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(
              color: isSelected ? color : theme.dividerColor,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? color : theme.textTheme.bodyLarge?.color,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  List<Map<String, String>> _getSampleQuestions(AppLocalizations loc) {
    return [
      {
        'question': isArabic
            ? 'ما هو الموضوع الرئيسي في المستند؟'
            : 'What is the main topic discussed in the document?',
        'answer': isArabic
            ? 'الموضوع الرئيسي هو الذكاء الاصطناعي وتطبيقاته.'
            : 'The main topic is artificial intelligence and its applications.',
        'type': loc.multipleChoice,
        'difficulty': loc.easy,
      },
      {
        'question': isArabic
            ? 'صح أم خطأ: هل يذكر المستند خوارزميات التعلم الآلي؟'
            : 'True or False: The document mentions machine learning algorithms.',
        'answer': isArabic ? 'صح' : 'True',
        'type': loc.trueFalse,
        'difficulty': loc.easy,
      },
      {
        'question': isArabic
            ? 'اشرح النتائج الرئيسية للبحث.'
            : 'Explain the key findings of the research.',
        'answer': isArabic
            ? 'البحث أظهر تحسينات كبيرة في الكفاءة باستخدام تقنيات الذكاء الاصطناعي.'
            : 'The research found significant improvements in efficiency using AI technologies.',
        'type': loc.shortAnswer,
        'difficulty': loc.medium,
      },
    ];
  }

  // Helper function to get text by key from AppLocalizations
  String locByKey(AppLocalizations loc, String key) {
    switch (key) {
      case 'multipleChoice':
        return loc.multipleChoice;
      case 'trueFalse':
        return loc.trueFalse;
      case 'shortAnswer':
        return loc.shortAnswer;
      case 'easy':
        return loc.easy;
      case 'medium':
        return loc.medium;
      case 'hard':
        return loc.hard;
      default:
        return key;
    }
  }
}

class QuestionItem extends StatelessWidget {
  final ThemeData theme;
  final String question;
  final String answer;
  final String type;
  final String difficulty;
  final AppLocalizations loc;

  const QuestionItem({
    Key? key,
    required this.theme,
    required this.question,
    required this.answer,
    required this.type,
    required this.difficulty,
    required this.loc,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    Color difficultyColor = difficulty == loc.easy
        ? const Color(0xFF10B981)
        : difficulty == loc.medium
        ? const Color(0xFFF59E0B)
        : const Color(0xFFEF4444);

    Color typeColor = type == loc.multipleChoice
        ? const Color(0xFF6366F1)
        : type == loc.trueFalse
        ? const Color(0xFF10B981)
        : const Color(0xFFF59E0B);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Material(
        color: Colors.transparent,
        child: Container(
          decoration: BoxDecoration(
            color: theme.scaffoldBackgroundColor,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: theme.brightness == Brightness.dark
                    ? Colors.black.withOpacity(0.3)
                    : Colors.black.withOpacity(0.04),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: typeColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            type == loc.multipleChoice
                                ? Icons.quiz_rounded
                                : type == loc.trueFalse
                                ? Icons.check_circle_outline_rounded
                                : Icons.edit_note_rounded,
                            size: 14,
                            color: typeColor,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            type,
                            style: TextStyle(
                              color: typeColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: difficultyColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            difficulty == loc.easy
                                ? Icons.sentiment_satisfied_rounded
                                : difficulty == loc.medium
                                ? Icons.sentiment_neutral_rounded
                                : Icons.sentiment_very_dissatisfied_rounded,
                            size: 14,
                            color: difficultyColor,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            difficulty,
                            style: TextStyle(
                              color: difficultyColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  question,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        theme.cardColor,
                        theme.cardColor.withOpacity(0.8),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: theme.dividerColor.withOpacity(0.5),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(4),
                            decoration: BoxDecoration(
                              color: const Color(0xFF10B981).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(
                              Icons.lightbulb_outline_rounded,
                              size: 16,
                              color: Color(0xFF10B981),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            loc.answer,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: const Color(0xFF10B981),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        answer,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}