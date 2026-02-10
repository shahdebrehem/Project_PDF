// pages/home_page.dart
import 'package:flutter/material.dart';
import 'package:project_flutter/pages/sign_in_page.dart';
import 'translation_page.dart';
import 'summary_page.dart';
import 'splash_screen.dart';
import 'questions_page.dart';
import 'personal_page.dart';
import 'settings_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String? _selectedFileName;

  final List<Map<String, dynamic>> _recentFiles = [
    {'name': 'Research_Paper.pdf', 'date': '2024-01-15', 'type': 'Summary'},
    {'name': 'Project_Report.pdf', 'date': '2024-01-14', 'type': 'Translation'},
    {'name': 'Technical_Docs.pdf', 'date': '2024-01-13', 'type': 'Questions'},
  ];

  final List<Feature> _features = [
    Feature(
      title: 'Summarize',
      description: 'Get a concise summary of your PDF document',
      icon: Icons.description_outlined,
      color: Color(0xFF64B5F6),
      route: '/summary',
    ),
    Feature(
      title: 'Translate',
      description: 'Translate your PDF to any language',
      icon: Icons.translate_rounded,
      color: Color(0xFF81C784),
      route: '/translation',
    ),
    Feature(
      title: 'Questions',
      description: 'Generate questions from your content',
      icon: Icons.quiz_outlined,
      color: Color(0xFFFFB74D),
      route: '/questions',
    ),
  ];

  void _pickPDF() {
    setState(() {
      _selectedFileName = 'document.pdf';
    });
  }

  void _changePDF() {
    setState(() {
      _selectedFileName = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('SmartPDF'),
        backgroundColor: theme.cardColor,
        foregroundColor: theme.textTheme.bodyLarge?.color,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.person_rounded),
            onPressed: () {
              Navigator.push(context, MaterialPageRoute(builder: (context) => const PersonalPage()));
            },
          ),
        ],
      ),
      drawer: const AppDrawer(),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Upload Section
            Container(
              width: double.infinity,
              color: theme.cardColor,
              padding: const EdgeInsets.fromLTRB(24, 40, 24, 40),
              child: Column(
                children: [
                  Text(
                    'Upload your PDF',
                    style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Choose a PDF file to get started',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Upload Button
                  if (_selectedFileName == null)
                    Container(
                      width: double.infinity,
                      height: 200,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Color(0xFF64B5F6), Color(0xFF4DD0E1)],
                        ),
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(theme.brightness == Brightness.dark ? 0.5 : 0.3),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: _pickPDF,
                          borderRadius: BorderRadius.circular(24),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(20),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.3),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.upload_file_rounded, size: 48, color: Colors.white),
                              ),
                              const SizedBox(height: 16),
                              const Text(
                                'Upload File',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.w600,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    )
                  else
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: const Color(0xFF81C784).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFF81C784), width: 2),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF81C784),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(Icons.check_rounded, color: Colors.white, size: 24),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _selectedFileName!,
                                  style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Ready to process',
                                  style: TextStyle(color: Color(0xFF81C784), fontSize: 14),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            onPressed: _changePDF,
                            icon: Icon(Icons.close_rounded, color: theme.iconTheme.color?.withOpacity(0.7)),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // AI Features Section
            Container(
              color: theme.scaffoldBackgroundColor,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('AI Features', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 24),

                  // Features List
                  ..._features.map((feature) => _buildFeatureItem(context, theme, feature)),

                  const SizedBox(height: 32),

                  // Recent Files
                  Text('Recent Files', style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  ..._recentFiles.map((file) => _buildRecentFileItem(theme, file)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(BuildContext context, ThemeData theme, Feature feature) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(theme.brightness == Brightness.dark ? 0.5 : 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            if (feature.route == '/translation') {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const TranslationPage()));
            } else if (feature.route == '/summary') {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const SummaryPage()));
            } else if (feature.route == '/questions') {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const QuestionsPage()));
            }
          },
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: feature.color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(feature.icon, color: feature.color, size: 32),
                ),
                const SizedBox(width: 20),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(feature.title,
                          style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600)),
                      const SizedBox(height: 4),
                      Text(
                        feature.description,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.arrow_forward_ios_rounded,
                    color: theme.textTheme.bodyMedium?.color?.withOpacity(0.5), size: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRecentFileItem(ThemeData theme, Map<String, dynamic> file) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(theme.brightness == Brightness.dark ? 0.5 : 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: theme.brightness == Brightness.dark
                  ? Colors.grey.shade800
                  : Colors.grey.shade100,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.description_outlined,
                color: theme.brightness == Brightness.dark ? Colors.grey.shade400 : Colors.grey.shade600,
                size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(file['name'],
                    style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text('${file['type']} • ${file['date']}',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                      fontSize: 13,
                    )),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.more_vert_rounded,
                color: theme.iconTheme.color?.withOpacity(0.7)),
            onPressed: () {},
          ),
        ],
      ),
    );
  }
}

class Feature {
  final String title;
  final String description;
  final IconData icon;
  final Color color;
  final String route;

  Feature({
    required this.title,
    required this.description,
    required this.icon,
    required this.color,
    required this.route,
  });
}

class AppDrawer extends StatelessWidget {
  const AppDrawer({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF64B5F6), Color(0xFF4DD0E1)],
              ),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.white,
                  child: Icon(Icons.person_rounded, color: Color(0xFF64B5F6), size: 30),
                ),
                SizedBox(height: 12),
                Text('Ahmed Mohamed',
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                Text('ahmed@example.com', style: TextStyle(color: Colors.white70)),
              ],
            ),
          ),
          _buildDrawerItem(context, Icons.home_rounded, 'Home', () {
            Navigator.pop(context);
          }, theme: theme),
          _buildDrawerItem(context, Icons.translate_rounded, 'Translation', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const TranslationPage()));
          }, theme: theme),
          _buildDrawerItem(context, Icons.summarize_rounded, 'Summary', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const SummaryPage()));
          }, theme: theme),
          _buildDrawerItem(context, Icons.quiz_rounded, 'Questions', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const QuestionsPage()));
          }, theme: theme),
          _buildDrawerItem(context, Icons.person_rounded, 'Personal Page', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const PersonalPage()));
          }, theme: theme),
          _buildDrawerItem(context, Icons.settings_rounded, 'Settings', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsPage()));
          }, theme: theme),
          const Divider(),
          _buildDrawerItem(context, Icons.logout_rounded, 'Logout', () {
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const SplashScreen()));
          }, color: Colors.red, theme: theme),
        ],
      ),
    );
  }

  Widget _buildDrawerItem(BuildContext context, IconData icon, String title, VoidCallback onTap,
      {Color? color, required ThemeData theme}) {
    return ListTile(
      leading: Icon(icon, color: color ?? theme.iconTheme.color),
      title: Text(title, style: TextStyle(color: color ?? theme.textTheme.bodyLarge?.color)),
      onTap: onTap,
    );
  }
}
