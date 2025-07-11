import 'package:flutter/material.dart';
import '../features/search/search_screen.dart';
import '../features/library/library_screen.dart';
import '../features/debug/audio_debug_screen.dart';
import '../main_navigation.dart';

class AppRoutes {
  static const String home = '/';
  static const String search = '/search';
  static const String library = '/library';
  static const String player = '/player';
  static const String profile = '/profile';
  static const String audioDebug = '/audio-debug';

  static Map<String, WidgetBuilder> get routes {
    return {
      home: (context) => const MainNavigation(),
      search: (context) => const SearchScreen(),
      library: (context) => const LibraryScreen(),
      audioDebug: (context) => const AudioDebugScreen(),
      // Add more routes as we create more screens
    };
  }

  static Route<dynamic>? onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case home:
        return MaterialPageRoute(builder: (context) => const MainNavigation());
      case search:
        return MaterialPageRoute(builder: (context) => const SearchScreen());
      case library:
        return MaterialPageRoute(builder: (context) => const LibraryScreen());
      case audioDebug:
        return MaterialPageRoute(
          builder: (context) => const AudioDebugScreen(),
        );
      default:
        return MaterialPageRoute(
          builder:
              (context) =>
                  const Scaffold(body: Center(child: Text('Page not found'))),
        );
    }
  }
}
