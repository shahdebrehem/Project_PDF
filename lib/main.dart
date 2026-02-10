import 'package:flutter/material.dart';
import 'pages/splash_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);

  static _MyAppState of(BuildContext context) {
    return context.findAncestorStateOfType<_MyAppState>()!;
  }

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  ThemeMode themeMode = ThemeMode.light;

  void changeTheme(ThemeMode mode) {
    setState(() {
      themeMode = mode;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartPDF',
      debugShowCheckedModeBanner: false,

      /// 👈 هنا التحكم في Dark / Light
      themeMode: themeMode,

      /// 🌞 Light Theme
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        primaryColor: const Color(0xFF64B5F6),
        scaffoldBackgroundColor: Colors.white,
        fontFamily: 'Inter',
      ),

      /// 🌙 Dark Theme
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF64B5F6),
        scaffoldBackgroundColor: const Color(0xFF121212),
        fontFamily: 'Inter',
      ),

      home: const SplashScreen(),
    );
  }
}
