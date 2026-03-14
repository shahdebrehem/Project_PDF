import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:project_flutter/services/auth_service.dart';
import 'package:project_flutter/services/files_service.dart';
import 'translation_page.dart';
import 'summary_page.dart';
import 'questions_page.dart';
import 'personal_page.dart';
import 'settings_page.dart';
import 'sign_in_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final AuthService _authService = AuthService();
  final FilesService _filesService = FilesService();

  Map<String, dynamic>? _user;
  List<Map<String, dynamic>> _recentFiles = [];
  bool _isLoading = true;
  bool _isLoadingFiles = true;
  String? _selectedFileName;

  final List<Feature> _features = [
    Feature(
      title: 'Summarize',
      description: 'Get a concise summary of your PDF document',
      icon: Icons.description_outlined,
      color: const Color(0xFF64B5F6),
      route: '/summary',
    ),
    Feature(
      title: 'Translate',
      description: 'Translate your PDF to any language',
      icon: Icons.translate_rounded,
      color: const Color(0xFF81C784),
      route: '/translation',
    ),
    Feature(
      title: 'Questions',
      description: 'Generate questions from your content',
      icon: Icons.quiz_outlined,
      color: const Color(0xFFFFB74D),
      route: '/questions',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    setState(() => _isLoading = true);

    final localUser = await _authService.getCurrentUserFromStorage();

    if (localUser != null) {
      setState(() {
        _user = localUser;
        _isLoading = false;
      });

      await _loadRecentFiles();
      _refreshUserData();
    } else {
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const SignInPage()),
        );
      }
    }
  }

  Future<void> _loadRecentFiles() async {
    setState(() => _isLoadingFiles = true);

    final files = await _filesService.getRecentFiles();

    if (mounted) {
      setState(() {
        _recentFiles = files;
        _isLoadingFiles = false;
      });
    }
  }

  Future<void> _refreshUserData() async {
    try {
      final response = await _authService.getCurrentUser();
      if (response['success'] == true) {
        setState(() {
          _user = response['data'];
        });
      }
    } catch (e) {
      debugPrint('Error refreshing user: $e');
    }
  }

  String _getInitials(String? name) {
    if (name == null || name.isEmpty) return 'U';
    final parts = name.split(' ');
    if (parts.length > 1) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name[0].toUpperCase();
  }

  Color _getColorFromName(String? name) {
    if (name == null || name.isEmpty) return const Color(0xFF64B5F6);
    final hash = name.hashCode.abs();
    final hue = hash % 360;
    return HSLColor.fromAHSL(1.0, hue.toDouble(), 0.7, 0.5).toColor();
  }

  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Logout'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await _authService.logout();
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const SignInPage()),
        );
      }
    }
  }

  // pages/home_page.dart - تعديل دالة _pickPDF
  Future<void> _pickPDF() async {
    try {
      // استخدام FilePicker لاختيار ملف PDF
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        allowMultiple: false,
      );

      if (result == null) {
        return; // المستخدم ألغى الاختيار
      }

      String? filePath = result.files.single.path;
      if (filePath == null) return;

      setState(() {
        _isLoadingFiles = true;
      });

      // رفع الملف
      final uploadedFile = await _filesService.uploadFile(
        File(filePath),
        type: 'PDF',
      );

      if (uploadedFile != null) {
        setState(() {
          _selectedFileName = result.files.single.name;
        });

        // تحديث قائمة الملفات
        await _loadRecentFiles();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('File uploaded successfully: ${result.files.single.name}'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to upload file'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      print('Error picking file: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingFiles = false;
        });
      }
    }
  }

  void _changePDF() {
    setState(() {
      _selectedFileName = null;
    });
  }

  Future<void> _deleteFile(String fileId, String fileName) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete File'),
        content: Text('Are you sure you want to delete "$fileName"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      final success = await _filesService.deleteFile(fileId);
      if (success) {
        _loadRecentFiles();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('File deleted successfully'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_isLoading) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 20),
              Text('Loading...', style: theme.textTheme.bodyMedium),
            ],
          ),
        ),
      );
    }

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
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => PersonalPage(user: _user),
                ),
              );
            },
          ),
        ],
      ),
      drawer: AppDrawer(
        user: _user,
        onLogout: _logout,
      ),
      body: RefreshIndicator(
        onRefresh: _loadRecentFiles,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: double.infinity,
                color: theme.cardColor,
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Welcome back,',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                      ),
                    ),
                    Text(
                      _user?['name'] ?? 'User',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _user?['email'] ?? '',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.textTheme.bodyMedium?.color?.withOpacity(0.5),
                      ),
                    ),
                  ],
                ),
              ),

              Container(
                width: double.infinity,
                color: theme.cardColor,
                padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
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

                    if (_selectedFileName == null)
                      _buildUploadButton(theme)
                    else
                      _buildSelectedFile(theme),
                  ],
                ),
              ),

              const SizedBox(height: 8),

              Container(
                color: theme.scaffoldBackgroundColor,
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('AI Features', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 24),
                    ..._features.map((feature) => _buildFeatureItem(context, theme, feature)),
                    const SizedBox(height: 32),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Recent Files',
                          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        if (_recentFiles.isNotEmpty)
                          TextButton(
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => PersonalPage(user: _user),
                                ),
                              );
                            },
                            child: const Text('View All'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    if (_isLoadingFiles)
                      const Center(child: Padding(
                        padding: EdgeInsets.all(20),
                        child: CircularProgressIndicator(),
                      ))
                    else if (_recentFiles.isEmpty)
                      _buildEmptyFiles(theme)
                    else
                      ..._recentFiles.take(5).map((file) => _buildRecentFileItem(theme, file)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUploadButton(ThemeData theme) {
    return Container(
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
    );
  }

  Widget _buildSelectedFile(ThemeData theme) {
    return Container(
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
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
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
    );
  }

  Widget _buildEmptyFiles(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Icon(
            Icons.folder_open_rounded,
            size: 50,
            color: theme.textTheme.bodyMedium?.color?.withOpacity(0.3),
          ),
          const SizedBox(height: 10),
          Text(
            'No files yet',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.textTheme.bodyMedium?.color?.withOpacity(0.5),
            ),
          ),
          const SizedBox(height: 5),
          Text(
            'Upload your first PDF to get started',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.textTheme.bodyMedium?.color?.withOpacity(0.3),
            ),
          ),
        ],
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
            if (_selectedFileName == null) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Please upload a PDF first'),
                  backgroundColor: Colors.orange,
                ),
              );
              return;
            }

            if (feature.route == '/translation') {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => TranslationPage(fileName: _selectedFileName),
                ),
              );
            } else if (feature.route == '/summary') {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => SummaryPage(fileName: _selectedFileName),
                ),
              );
            } else if (feature.route == '/questions') {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => QuestionsPage(fileName: _selectedFileName),
                ),
              );
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
    IconData getFileIcon() {
      switch (file['type']?.toLowerCase()) {
        case 'summary':
          return Icons.description_outlined;
        case 'translation':
          return Icons.translate_rounded;
        case 'questions':
          return Icons.quiz_outlined;
        default:
          return Icons.description_outlined;
      }
    }

    Color getFileColor() {
      switch (file['type']?.toLowerCase()) {
        case 'summary':
          return const Color(0xFF64B5F6);
        case 'translation':
          return const Color(0xFF81C784);
        case 'questions':
          return const Color(0xFFFFB74D);
        default:
          return Colors.grey;
      }
    }

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
              color: getFileColor().withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(getFileIcon(), color: getFileColor(), size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  file['name'],
                  style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      file['type'],
                      style: TextStyle(color: getFileColor(), fontSize: 12, fontWeight: FontWeight.w500),
                    ),
                    Text(
                      ' • ',
                      style: TextStyle(color: theme.textTheme.bodyMedium?.color?.withOpacity(0.5)),
                    ),
                    Text(
                      file['date'],
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          PopupMenuButton<String>(
            icon: Icon(Icons.more_vert_rounded, color: theme.iconTheme.color?.withOpacity(0.7)),
            onSelected: (value) {
              if (value == 'delete') {
                _deleteFile(file['id'], file['name']);
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'open',
                child: Row(
                  children: [Icon(Icons.visibility, size: 20), SizedBox(width: 8), Text('Open')],
                ),
              ),
              const PopupMenuItem(
                value: 'delete',
                child: Row(
                  children: [Icon(Icons.delete, size: 20, color: Colors.red), SizedBox(width: 8), Text('Delete', style: TextStyle(color: Colors.red))],
                ),
              ),
            ],
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

class AppDrawer extends StatelessWidget{
  final Map<String, dynamic>? user;
  final VoidCallback onLogout;

  const AppDrawer({Key? key, required this.user, required this.onLogout}) : super(key: key);

  String _getInitials(String? name) {
    if (name == null || name.isEmpty) return 'U';
    final parts = name.split(' ');
    if (parts.length > 1) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name[0].toUpperCase();
  }

  Color _getColorFromName(String? name) {
    if (name == null || name.isEmpty) return const Color(0xFF64B5F6);
    final hash = name.hashCode.abs();
    final hue = hash % 360;
    return HSLColor.fromAHSL(1.0, hue.toDouble(), 0.7, 0.5).toColor();
  }

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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.white,
                  child: Text(
                    _getInitials(user?['name']),
                    style: TextStyle(
                      color: _getColorFromName(user?['name']),
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  user?['name'] ?? 'User',
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Text(
                  user?['email'] ?? 'user@example.com',
                  style: const TextStyle(color: Colors.white70),
                ),
              ],
            ),
          ),
          _buildDrawerItem(
            context,
            Icons.home_rounded,
            'Home',
                () => Navigator.pop(context),
            theme: theme,
          ),
          _buildDrawerItem(
            context,
            Icons.person_rounded,
            'My Documents',
                () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => PersonalPage(user: user)),
              );
            },
              theme: theme),
          _buildDrawerItem(context, Icons.translate_rounded, 'Translation', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const TranslationPage()));
          }, theme: theme),
          _buildDrawerItem(context, Icons.summarize_rounded, 'Summary', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const SummaryPage()));
          }, theme: theme),
          _buildDrawerItem(context, Icons.quiz_rounded, 'Questions', () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const QuestionsPage()));
          }, theme: theme),
          _buildDrawerItem(
            context,
            Icons.settings_rounded,
            'Settings',
                () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsPage()),
              );
            },
            theme: theme,
          ),
          const Divider(),
          _buildDrawerItem(
            context,
            Icons.logout_rounded,
            'Logout',
                () {
              Navigator.pop(context);
              onLogout();
            },
            color: Colors.red,
            theme: theme,
          ),
        ],
      ),
    );
  }

  Widget _buildDrawerItem(
      BuildContext context,
      IconData icon,
      String title,
      VoidCallback onTap, {
        Color? color,
        required ThemeData theme,
      }) {
    return ListTile(
      leading: Icon(icon, color: color ?? theme.iconTheme.color),
      title: Text(title, style: TextStyle(color: color ?? theme.textTheme.bodyLarge?.color)),
      onTap: onTap,
    );
  }
}
