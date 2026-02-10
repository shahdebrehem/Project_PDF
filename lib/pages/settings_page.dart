import 'package:flutter/material.dart';
import '../main.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({Key? key}) : super(key: key);

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _notificationsEnabled = true;
  bool _autoSaveEnabled = false;
  String _selectedLanguage = 'english';

  final List<Map<String, dynamic>> _languages = [
    {'value': 'english', 'label': 'English'},
    {'value': 'arabic', 'label': 'Arabic'},
    {'value': 'spanish', 'label': 'Spanish'},
    {'value': 'french', 'label': 'French'},
  ];

  @override
  Widget build(BuildContext context) {
    final isDark =
        Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: const Text('Settings'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            /// Header
            Container(
              width: double.infinity,
              color: Theme.of(context).cardColor,
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Settings',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Customize your app experience',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            /// Language
            _section(
              context,
              title: 'Language & Region',
              subtitle: 'Choose your preferred language',
              child: Container(
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  children: _languages.map(
                        (language) => _buildLanguageOption(
                      context,
                      label: language['label'],
                      value: language['value'],
                      isSelected:
                      _selectedLanguage == language['value'],
                    ),
                  ).toList(),
                ),
              ),
            ),

            const SizedBox(height: 8),

            /// App Settings
            _section(
              context,
              title: 'App Settings',
              subtitle: 'Customize how the app behaves',
              child: Column(
                children: [
                  _buildSettingItem(
                    context,
                    icon: Icons.dark_mode_rounded,
                    title: 'Dark Mode',
                    subtitle: 'Switch to dark theme',
                    trailing: Switch(
                      value: isDark,
                      onChanged: (value) {
                        MyApp.of(context).changeTheme(
                          value
                              ? ThemeMode.dark
                              : ThemeMode.light,
                        );
                      },
                    ),
                  ),
                  _buildSettingItem(
                    context,
                    icon: Icons.notifications_rounded,
                    title: 'Push Notifications',
                    subtitle: 'Receive app notifications',
                    trailing: Switch(
                      value: _notificationsEnabled,
                      onChanged: (value) {
                        setState(() {
                          _notificationsEnabled = value;
                        });
                      },
                    ),
                  ),
                  _buildSettingItem(
                    context,
                    icon: Icons.save_rounded,
                    title: 'Auto Save',
                    subtitle: 'Automatically save your work',
                    trailing: Switch(
                      value: _autoSaveEnabled,
                      onChanged: (value) {
                        setState(() {
                          _autoSaveEnabled = value;
                        });
                      },
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 8),

            /// About
            _section(
              context,
              title: 'About',
              child: Column(
                children: const [
                  _InfoRow(title: 'App Version', value: '1.0.0'),
                  _InfoRow(
                      title: 'Build Number',
                      value: '2024.01.001'),
                  _InfoRow(
                      title: 'Last Updated',
                      value: 'January 15, 2024'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// ================= Helpers =================

  Widget _section(
      BuildContext context, {
        required String title,
        String? subtitle,
        required Widget child,
      }) {
    return Container(
      color: Theme.of(context).cardColor,
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style:
              Theme.of(context).textTheme.titleLarge),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(subtitle,
                style:
                Theme.of(context).textTheme.bodyMedium),
          ],
          const SizedBox(height: 20),
          child,
        ],
      ),
    );
  }

  Widget _buildLanguageOption(
      BuildContext context, {
        required String label,
        required String value,
        required bool isSelected,
      }) {
    return ListTile(
      onTap: () {
        setState(() {
          _selectedLanguage = value;
        });
      },
      title: Text(label),
      trailing: isSelected
          ? const Icon(Icons.check_rounded)
          : null,
    );
  }

  Widget _buildSettingItem(
      BuildContext context, {
        required IconData icon,
        required String title,
        required String subtitle,
        required Widget trailing,
      }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListTile(
        leading: Icon(icon),
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: trailing,
      ),
    );
  }
}

/// Info Row
class _InfoRow extends StatelessWidget {
  final String title;
  final String value;

  const _InfoRow({
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title,
              style:
              Theme.of(context).textTheme.bodyMedium),
          Text(value,
              style:
              Theme.of(context).textTheme.bodyLarge),
        ],
      ),
    );
  }
}
