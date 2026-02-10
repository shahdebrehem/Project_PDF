import 'package:flutter/material.dart';

class QuestionsPage extends StatefulWidget {
  const QuestionsPage({Key? key}) : super(key: key);

  @override
  State<QuestionsPage> createState() => _QuestionsPageState();
}

class _QuestionsPageState extends State<QuestionsPage> {
  String _selectedQuestionType = 'multiple';
  String _selectedDifficulty = 'medium';
  bool _isGenerating = false;

  final List<Map<String, dynamic>> _questionTypes = [
    {'value': 'multiple', 'label': 'Multiple Choice'},
    {'value': 'truefalse', 'label': 'True/False'},
    {'value': 'short', 'label': 'Short Answer'},
  ];

  final List<Map<String, dynamic>> _difficulties = [
    {'value': 'easy', 'label': 'Easy'},
    {'value': 'medium', 'label': 'Medium'},
    {'value': 'hard', 'label': 'Hard'},
  ];

  void _generateQuestions() {
    setState(() {
      _isGenerating = true;
    });

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isGenerating = false;
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
        title: const Text('Questions Generator'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              color: theme.cardColor,
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Questions Generator',
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Icon(Icons.description_outlined,
                          color: theme.iconTheme.color, size: 20),
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

            // Configuration Section
            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Configuration',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Question Type Selection
                  Text(
                    'Question Type',
                    style: theme.textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: _questionTypes.map((type) => _buildOptionChip(
                      theme: theme,
                      label: type['label'],
                      value: type['value'],
                      groupValue: _selectedQuestionType,
                      onSelected: (value) {
                        setState(() {
                          _selectedQuestionType = value;
                        });
                      },
                    )).toList(),
                  ),

                  const SizedBox(height: 24),

                  // Difficulty Selection
                  Text(
                    'Difficulty Level',
                    style: theme.textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: _difficulties.map((difficulty) => _buildOptionChip(
                      theme: theme,
                      label: difficulty['label'],
                      value: difficulty['value'],
                      groupValue: _selectedDifficulty,
                      onSelected: (value) {
                        setState(() {
                          _selectedDifficulty = value;
                        });
                      },
                    )).toList(),
                  ),

                  const SizedBox(height: 32),

                  // Generate Button
                  SizedBox(
                    width: double.infinity,
                    child: InkWell(
                      onTap: _isGenerating ? null : _generateQuestions,
                      borderRadius: BorderRadius.circular(16),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: _isGenerating
                                ? [
                              theme.disabledColor,
                              theme.disabledColor.withOpacity(0.8),
                            ]
                                : [
                              theme.colorScheme.primary,
                              theme.colorScheme.secondary,
                            ],
                          ),
                          borderRadius: BorderRadius.circular(16),
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
                              const Icon(Icons.quiz_rounded,
                                  color: Colors.white, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              _isGenerating ? 'Generating Questions...' : 'Generate Questions',
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
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Questions Result Section
            Container(
              color: theme.cardColor,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Generated Questions',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Questions based on your document content',
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 20),

                  ..._getSampleQuestions().map((question) => QuestionItem(
                    theme: theme,
                    question: question['question']!,
                    answer: question['answer']!,
                    type: question['type']!,
                    difficulty: question['difficulty']!,
                  )),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionChip({
    required ThemeData theme,
    required String label,
    required String value,
    required String groupValue,
    required Function(String) onSelected,
  }) {
    bool isSelected = groupValue == value;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => onSelected(value),
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            color: isSelected
                ? theme.colorScheme.primary.withOpacity(0.1)
                : theme.dividerColor.withOpacity(0.05),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected ? theme.colorScheme.primary : theme.dividerColor,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? theme.colorScheme.primary : theme.textTheme.bodyLarge?.color,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  List<Map<String, String>> _getSampleQuestions() {
    return [
      {
        'question': 'What is the main topic discussed in the document?',
        'answer': 'The main topic is artificial intelligence and its applications.',
        'type': 'Multiple Choice',
        'difficulty': 'Easy',
      },
      {
        'question': 'True or False: The document mentions machine learning algorithms.',
        'answer': 'True',
        'type': 'True/False',
        'difficulty': 'Easy',
      },
      {
        'question': 'Explain the key findings of the research.',
        'answer': 'The research found significant improvements in efficiency using AI technologies.',
        'type': 'Short Answer',
        'difficulty': 'Medium',
      },
    ];
  }
}

class QuestionItem extends StatelessWidget {
  final ThemeData theme;
  final String question;
  final String answer;
  final String type;
  final String difficulty;

  const QuestionItem({
    Key? key,
    required this.theme,
    required this.question,
    required this.answer,
    required this.type,
    required this.difficulty,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    Color difficultyColor = difficulty == 'Easy'
        ? Colors.green
        : difficulty == 'Medium'
        ? Colors.orange
        : Colors.red;

    Color typeColor = type == 'Multiple Choice'
        ? Colors.blue
        : type == 'True/False'
        ? Colors.green
        : Colors.orange;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: theme.scaffoldBackgroundColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {},
          borderRadius: BorderRadius.circular(16),
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
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        type,
                        style: TextStyle(
                          color: typeColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: difficultyColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        difficulty,
                        style: TextStyle(
                          color: difficultyColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  question,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
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
                        'Answer:',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        answer,
                        style: theme.textTheme.bodyMedium,
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
