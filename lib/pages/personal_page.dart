import 'package:flutter/material.dart';
import 'package:project_flutter/services/auth_service.dart';
import 'package:project_flutter/services/files_service.dart';

class PersonalPage extends StatefulWidget {
  final Map<String, dynamic>? user;

  const PersonalPage({Key? key, this.user}) : super(key: key);

  @override
  State<PersonalPage> createState() => _PersonalPageState();
}

class _PersonalPageState extends State<PersonalPage> {
  final AuthService _authService = AuthService();
  final FilesService _filesService = FilesService();

  Map<String, dynamic>? _user;
  List<Map<String, dynamic>> _userFiles = [];
  bool _isLoading = true;
  Map<String, int> _stats = {
    'completed': 0,
    'processing': 0,
    'total': 0,
  };

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    if (widget.user != null) {
      _user = widget.user;
    } else {
      _user = await _authService.getCurrentUserFromStorage();
    }

    await _loadUserFiles();
  }

  Future<void> _loadUserFiles() async {
    final files = await _filesService.getRecentFiles();

    int completed = files.where((f) => f['status'] == 'Completed').length;
    int processing = files.where((f) => f['status'] == 'Processing').length;

    if (mounted) {
      setState(() {
        _userFiles = files;
        _stats = {
          'completed': completed,
          'processing': processing,
          'total': files.length,
        };
        _isLoading = false;
      });
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
        _loadUserFiles();
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
        appBar: AppBar(
          title: const Text('My Documents'),
          backgroundColor: theme.cardColor,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('My Documents'),
        elevation: 0,
        backgroundColor: theme.cardColor,
        foregroundColor: theme.textTheme.bodyLarge?.color,
      ),
      body: RefreshIndicator(
        onRefresh: _loadUserFiles,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            children: [
              Container(
                width: double.infinity,
                color: theme.cardColor,
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
                            _getColorFromName(_user?['name']),
                            _getColorFromName(_user?['name']).withBlue(200),
                          ],
                        ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: _getColorFromName(_user?['name']).withOpacity(0.3),
                            blurRadius: 15,
                            offset: const Offset(0, 5),
                          ),
                        ],
                      ),
                      child: Center(
                        child: Text(
                          _getInitials(_user?['name']),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      _user?['name'] ?? 'User',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _user?['email'] ?? '',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _buildStatItem(theme, 'Completed', '${_stats['completed']}', const Color(0xFF81C784)),
                        _buildStatItem(theme, 'Processing', '${_stats['processing']}', const Color(0xFFFFB74D)),
                        _buildStatItem(theme, 'Total', '${_stats['total']}', const Color(0xFF64B5F6)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),

              Container(
                color: theme.cardColor,
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'All Documents',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Your processed PDF files',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                      ),
                    ),
                    const SizedBox(height: 20),

                    if (_userFiles.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(40),
                        child: Column(
                          children: [
                            Icon(
                              Icons.folder_open_rounded,
                              size: 60,
                              color: theme.textTheme.bodyMedium?.color?.withOpacity(0.3),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'No documents yet',
                              style: theme.textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Upload your first PDF to get started',
                              style: theme.textTheme.bodyMedium?.copyWith(
                                color: theme.textTheme.bodyMedium?.color?.withOpacity(0.5),
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      ..._userFiles.map((file) => _buildUserFileItem(theme, file)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatItem(ThemeData theme, String title, String value, Color color) {
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
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.textTheme.bodySmall?.color?.withOpacity(0.7),
          ),
        ),
      ],
    );
  }

  Widget _buildUserFileItem(ThemeData theme, Map<String, dynamic> file) {
    String status = file['status'] ?? 'Completed';
    Color statusColor = status == 'Completed' ? const Color(0xFF81C784) : const Color(0xFFFFB74D);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: theme.scaffoldBackgroundColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: theme.brightness == Brightness.dark
                ? Colors.black.withOpacity(0.3)
                : Colors.black.withOpacity(0.04),
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
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
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
                              status,
                              style: TextStyle(
                                color: statusColor,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '${file['type']} • ${file['date']}',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.bodyMedium?.copyWith(
                                color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (file['size'] != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          file['size'],
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.textTheme.bodySmall?.color?.withOpacity(0.6),
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.visibility_rounded, color: const Color(0xFF64B5F6)),
                  onPressed: () {},
                ),
                IconButton(
                  icon: Icon(Icons.download_rounded, color: const Color(0xFF81C784)),
                  onPressed: () {},
                ),
                PopupMenuButton<String>(
                  icon: Icon(Icons.more_vert_rounded, color: theme.iconTheme.color),
                  onSelected: (value) {
                    if (value == 'delete') {
                      _deleteFile(file['id'], file['name']);
                    }
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete, color: Colors.red, size: 20),
                          SizedBox(width: 8),
                          Text('Delete', style: TextStyle(color: Colors.red)),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Color _getTypeColor(String? type) {
    switch (type?.toLowerCase()) {
      case 'summary':
        return const Color(0xFF64B5F6);
      case 'translation':
        return const Color(0xFF81C784);
      case 'questions':
        return const Color(0xFFFFB74D);
      default:
        return const Color(0xFF64B5F6);
    }
  }

  IconData _getTypeIcon(String? type) {
    switch (type?.toLowerCase()) {
      case 'summary':
        return Icons.summarize_rounded;
      case 'translation':
        return Icons.translate_rounded;
      case 'questions':
        return Icons.quiz_rounded;
      default:
        return Icons.description_rounded;
    }
  }
}