// main.dart
import 'package:flutter/material.dart';
import 'pages/splash_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartPDF',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primaryColor: const Color(0xFF64B5F6),
        useMaterial3: true,
        fontFamily: 'Inter',
      ),
      home: const SplashScreen(), // ← صفحة البداية
    );
  }
}
