import 'package:flutter/material.dart';

/// Application constants and configuration values
class AppConstants {
  // App Info
  static const String appName = 'MREE';
  static const String appVersion = '1.0.0';
  static const String appDescription = 'Music streaming made simple';

  // Network Configuration
  static const String defaultPort = '8000';
  static const Duration defaultTimeout = Duration(seconds: 10);
  static const int maxRetries = 3;

  // UI Constants
  static const double defaultPadding = 16.0;
  static const double defaultRadius = 12.0;
  static const double defaultElevation = 4.0;

  // Audio Configuration
  static const List<String> supportedFormats = ['mp3', 'flac', 'ogg'];
  static const int defaultQuality = 192;

  // Search Configuration
  static const int defaultSearchLimit = 50;
  static const int maxSearchResults = 100;

  // Validation
  static const int minUsernameLength = 3;
  static const int maxUsernameLength = 50;
  static const int minPasswordLength = 6;

  // Storage Keys
  static const String serverIpKey = 'server_ip';
  static const String serverPortKey = 'server_port';
  static const String authTokenKey = 'auth_token';

  // Default Values
  static const String defaultServerHint = '192.168.1.100';
  static const String defaultPortHint = '8000';
}

/// Color palette for the app
class AppColors {
  static const Color primary = Color(0xFF1DB954); // Spotify green
  static const Color background = Color(0xFF121212);
  static const Color surface = Color(0xFF1E1E1E);
  static const Color card = Color(0xFF2A2A2A);
  static const Color error = Colors.red;
  static const Color success = Colors.green;
  static const Color warning = Colors.orange;
  static const Color info = Colors.blue;
}

/// Animation durations
class AppDurations {
  static const Duration fast = Duration(milliseconds: 200);
  static const Duration medium = Duration(milliseconds: 300);
  static const Duration slow = Duration(milliseconds: 500);
}

/// Network endpoints
class ApiEndpoints {
  static const String auth = '/auth';
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String search = '/search';
  static const String download = '/download';
  static const String health = '/health';
  static const String streaming = '/streaming';
}
