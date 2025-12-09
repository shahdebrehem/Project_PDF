// pages/personal_page.dart
import 'package:flutter/material.dart';

class PersonalPage extends StatelessWidget {
  const PersonalPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final List<Map<String, dynamic>> userFiles = [
      {
        'name': 'Research_Paper.pdf',
        'date': '2024-01-15',
        'type': 'Summary',
        'status': 'Completed',
        'size': '2.4 MB'
      },
      {
        'name': 'Project_Report.pdf',
        'date': '2024-01-14',
        'type': 'Translation',
        'status': 'Completed',
        'size': '1.8 MB'
      },
      {
        'name': 'Technical_Docs.pdf',
        'date': '2024-01-13',
        'type': 'Questions',
        'status': 'Processing',
        'size': '3.2 MB'
      },
      {
        'name': 'Thesis_Chapter1.pdf',
        'date': '2024-01-12',
        'type': 'Summary',
        'status': 'Completed',
        'size': '4.1 MB'
      },
      {
        'name': 'Meeting_Minutes.pdf',
        'date': '2024-01-11',
        'type': 'Translation',
        'status': 'Completed',
        'size': '1.2 MB'
      },
    ];

    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('My Documents'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.black87),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // User Info Section
            Container(
              width: double.infinity,
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 32),
              child: Column(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          Color(0xFF64B5F6),
                          Color(0xFF4DD0E1),
                        ],
                      ),
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Color(0xFF64B5F6).withOpacity(0.3),
                          blurRadius: 15,
                          offset: const Offset(0, 5),
                        ),
                      ],
                    ),
                    child: const Icon(
                        Icons.person_rounded,
                        color: Colors.white,
                        size: 40
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Ahmed Mohamed',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Premium User • ${userFiles.length} documents',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Stats Row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildStatItem('Completed', '4', Color(0xFF81C784)),
                      _buildStatItem('Processing', '1', Color(0xFFFFB74D)),
                      _buildStatItem('Total', '5', Color(0xFF64B5F6)),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // Documents List Section
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'All Documents',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Your processed PDF files',
                    style: TextStyle(
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Files List
                  ...userFiles.map((file) => _buildUserFileItem(file)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String title, String value, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          title,
          style: TextStyle(
            color: Colors.grey.shade600,
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  Widget _buildUserFileItem(Map<String, dynamic> file) {
    Color statusColor = file['status'] == 'Completed' ? Color(0xFF81C784) : Color(0xFFFFB74D);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
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
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _getTypeColor(file['type']).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    _getTypeIcon(file['type']),
                    color: _getTypeColor(file['type']),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        file['name'],
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: statusColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              file['status'],
                              style: TextStyle(
                                color: statusColor,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${file['type']} • ${file['date']}',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        file['size'],
                        style: TextStyle(
                          color: Colors.grey.shade500,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: Icon(
                    Icons.visibility_rounded,
                    color: Color(0xFF64B5F6),
                  ),
                  onPressed: () {},
                ),
                IconButton(
                  icon: Icon(
                    Icons.download_rounded,
                    color: Color(0xFF81C784),
                  ),
                  onPressed: () {},
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Color _getTypeColor(String type) {
    switch (type) {
      case 'Summary':
        return Color(0xFF64B5F6);
      case 'Translation':
        return Color(0xFF81C784);
      case 'Questions':
        return Color(0xFFFFB74D);
      default:
        return Color(0xFF64B5F6);
    }
  }

  IconData _getTypeIcon(String type) {
    switch (type) {
      case 'Summary':
        return Icons.summarize_rounded;
      case 'Translation':
        return Icons.translate_rounded;
      case 'Questions':
        return Icons.quiz_rounded;
      default:
        return Icons.description_rounded;
    }
  }
}