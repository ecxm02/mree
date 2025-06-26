import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../main_navigation.dart';

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Music Streaming App',
      theme: AppTheme.darkTheme,
      home: const MainNavigation(),
      debugShowCheckedModeBanner: false,
    );
  }
}
