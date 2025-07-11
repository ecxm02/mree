import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'features/home/home_screen.dart';
import 'features/search/search_screen.dart';
import 'features/library/library_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/auth/auth_provider.dart';
import 'features/player/mini_player.dart';
import 'core/services/audio_player_service.dart';

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const HomeScreen(),
    const SearchScreen(),
    const LibraryScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final audioPlayer = context.watch<AudioPlayerService>();
    final isPlayerActive = audioPlayer.currentSong != null;

    return Scaffold(
      appBar:
          _currentIndex == 0
              ? AppBar(
                title: const Text('MREE'),
                actions: [
                  IconButton(
                    icon: const Icon(Icons.person),
                    onPressed: () => _showProfileMenu(context),
                  ),
                ],
              )
              : null,
      body: Column(
        children: [
          Expanded(child: _screens[_currentIndex]),
          // Show mini player if a song is currently loaded
          if (isPlayerActive) const MiniPlayer(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
          BottomNavigationBarItem(
            icon: Icon(Icons.library_music),
            label: 'Your Library',
          ),
        ],
      ),
    );
  }

  void _showProfileMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder:
          (context) => Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.person),
                title: const Text('Profile'),
                onTap: () {
                  Navigator.pop(context);
                  // TODO: Navigate to profile screen
                },
              ),
              ListTile(
                leading: const Icon(Icons.settings),
                title: const Text('Settings'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const SettingsScreen(),
                    ),
                  );
                },
              ),
              ListTile(
                leading: const Icon(Icons.bug_report, color: Colors.red),
                title: const Text('Audio Debug'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.pushNamed(context, '/audio-debug');
                },
              ),
              ListTile(
                leading: const Icon(Icons.logout),
                title: const Text('Logout'),
                onTap: () async {
                  Navigator.pop(context);
                  await context.read<AuthProvider>().logout();
                },
              ),
            ],
          ),
    );
  }
}
