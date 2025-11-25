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
      appBar: AppBar(
        title: const Text('My Documents'),
        backgroundColor: Color(0xFF7C3AED),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // User Info
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Color(0xFF7C3AED).withOpacity(0.1),
                    Color(0xFF10B981).withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  Container(
                    width: 60,
                    height: 60,
                    decoration: const BoxDecoration(
                      color: Color(0xFF7C3AED),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.person_rounded, color: Colors.white, size: 30),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Ahmed Mohamed',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Premium User • ${userFiles.length} documents',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Documents List
            const Text(
              'All Documents',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            ...userFiles.map((file) => _buildUserFileItem(file)),
          ],
        ),
      ),
    );
  }

  Widget _buildUserFileItem(Map<String, dynamic> file) {
    Color statusColor = file['status'] == 'Completed' ? Colors.green : Colors.orange;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Icon(Icons.description_rounded, color: Colors.grey.shade600),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  file['name'],
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: statusColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: statusColor),
                      ),
                      child: Text(
                        file['status'],
                        style: TextStyle(color: statusColor, fontSize: 12),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${file['type']} • ${file['date']} • ${file['size']}',
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                    ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.visibility_rounded, color: Color(0xFF7C3AED)),
            onPressed: () {},
          ),
          IconButton(
            icon: Icon(Icons.download_rounded, color: Color(0xFF10B981)),
            onPressed: () {},
          ),
        ],
      ),
    );
  }
}