import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../core/services/server_config_service.dart';
import '../main_navigation.dart';
import '../features/auth/auth_provider.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/register_screen.dart';
import '../features/auth/server_setup_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/player/player.dart';
import '../features/debug/debug_info_screen.dart';

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  bool _hasServerConfig = false;
  bool _isCheckingServer = true;

  @override
  void initState() {
    super.initState();
    _checkServerConfig();
  }

  Future<void> _checkServerConfig() async {
    final hasConfig = await ServerConfigService.instance.hasServerConfig();
    setState(() {
      _hasServerConfig = hasConfig;
      _isCheckingServer = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MREE - Music Streaming',
      theme: AppTheme.darkTheme,
      debugShowCheckedModeBanner: false,
      home:
          _isCheckingServer
              ? const Scaffold(body: Center(child: CircularProgressIndicator()))
              : !_hasServerConfig
              ? const ServerSetupScreen()
              : Consumer<AuthProvider>(
                builder: (context, authProvider, child) {
                  if (authProvider.isLoading) {
                    return const Scaffold(
                      body: Center(child: CircularProgressIndicator()),
                    );
                  }

                  return authProvider.isAuthenticated
                      ? const MainNavigation()
                      : const LoginScreen();
                },
              ),
      routes: {
        '/server-setup': (context) => const ServerSetupScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/main': (context) => const MainNavigation(),
        '/settings': (context) => const SettingsScreen(),
        '/now-playing': (context) => const NowPlayingScreen(),
        '/debug': (context) => const DebugInfoScreen(),
      },
    );
  }
}
