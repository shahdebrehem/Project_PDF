// pages/questions_page.dart
import 'package:flutter/material.dart';

class QuestionsPage extends StatelessWidget {
  const QuestionsPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Questions Generator'),
        backgroundColor: Color(0xFFF59E0B),
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Filter Options
            Wrap(
              spacing: 16,
              runSpacing: 16,
              children: [
                SizedBox(
                  width: 200,
                  child: DropdownButtonFormField(
                    value: 'multiple',
                    items: const [
                      DropdownMenuItem(value: 'multiple', child: Text('Multiple Choice')),
                      DropdownMenuItem(value: 'truefalse', child: Text('True/False')),
                      DropdownMenuItem(value: 'short', child: Text('Short Answer')),
                    ],
                    onChanged: (value) {},
                    decoration: const InputDecoration(
                      labelText: 'Question Type',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                SizedBox(
                  width: 200,
                  child: DropdownButtonFormField(
                    value: 'medium',
                    items: const [
                      DropdownMenuItem(value: 'easy', child: Text('Easy')),
                      DropdownMenuItem(value: 'medium', child: Text('Medium')),
                      DropdownMenuItem(value: 'hard', child: Text('Hard')),
                    ],
                    onChanged: (value) {},
                    decoration: const InputDecoration(
                      labelText: 'Difficulty',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            // Questions List
            Expanded(
              child: ListView(
                children: const [
                  QuestionItem(
                    question: 'What is the main topic discussed in the document?',
                    answer: 'The main topic is artificial intelligence and its applications.',
                    type: 'Multiple Choice',
                    difficulty: 'Easy',
                  ),
                  QuestionItem(
                    question: 'True or False: The document mentions machine learning algorithms.',
                    answer: 'True',
                    type: 'True/False',
                    difficulty: 'Easy',
                  ),
                  QuestionItem(
                    question: 'Explain the key findings of the research.',
                    answer: 'The research found significant improvements in efficiency using AI technologies.',
                    type: 'Short Answer',
                    difficulty: 'Medium',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // Download Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {},
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      side: const BorderSide(color: Color(0xFFF59E0B)),
                    ),
                    child: const Text('Download JSON'),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Color(0xFFF59E0B),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text('Download Excel'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class QuestionItem extends StatelessWidget {
  final String question;
  final String answer;
  final String type;
  final String difficulty;

  const QuestionItem({
    Key? key,
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

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFFF59E0B).withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Color(0xFFF59E0B).withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Color(0xFFF59E0B),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  type,
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: difficultyColor,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  difficulty,
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            question,
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            'Answer: $answer',
            style: TextStyle(color: Colors.grey.shade700),
          ),
        ],
      ),
    );
  }
}