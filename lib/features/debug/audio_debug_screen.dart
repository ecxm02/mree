import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/audio_player_service.dart';
import '../../core/services/api_service.dart';
import 'quick_login_screen.dart';

class AudioDebugScreen extends StatefulWidget {
  const AudioDebugScreen({super.key});

  @override
  State<AudioDebugScreen> createState() => _AudioDebugScreenState();
}

class _AudioDebugScreenState extends State<AudioDebugScreen> {
  String _debugOutput = '';
  bool _isLoading = false;

  void _addDebugLine(String line) {
    setState(() {
      _debugOutput += '${DateTime.now().toIso8601String()}: $line\n';
    });
  }

  @override
  Widget build(BuildContext context) {
    final audioPlayer = context.watch<AudioPlayerService>();
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Audio Debug'),
        backgroundColor: Colors.red,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Current status
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Audio Player Status',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text('Is Playing: ${audioPlayer.isPlaying}'),
                    Text('Is Loading: ${audioPlayer.isLoading}'),
                    Text('Current Song: ${audioPlayer.currentSong?.title ?? 'None'}'),
                    Text('Position: ${audioPlayer.position.toString()}'),
                    Text('Duration: ${audioPlayer.duration.toString()}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // Test buttons
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ElevatedButton(
                  onPressed: _isLoading ? null : _testConnectivity,
                  child: const Text('Test Connectivity'),
                ),
                ElevatedButton(
                  onPressed: _isLoading ? null : _showQuickLogin,
                  child: const Text('Quick Login'),
                ),
                ElevatedButton(
                  onPressed: _isLoading ? null : _testLibrary,
                  child: const Text('Test Library'),
                ),
                ElevatedButton(
                  onPressed: _isLoading ? null : _testPlayFirstSong,
                  child: const Text('Play First Song'),
                ),
                ElevatedButton(
                  onPressed: _clearDebugOutput,
                  child: const Text('Clear Log'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Debug output
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: SingleChildScrollView(
                    child: Text(
                      _debugOutput.isEmpty ? 'No debug output yet' : _debugOutput,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontFamily: 'monospace',
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _testConnectivity() async {
    setState(() => _isLoading = true);
    _addDebugLine('🔍 Starting connectivity test...');
    
    try {
      final audioPlayer = context.read<AudioPlayerService>();
      await audioPlayer.testConnectivity();
      _addDebugLine('✅ Connectivity test completed - check debug console for details');
    } catch (e) {
      _addDebugLine('❌ Connectivity test failed: $e');
    }
    
    setState(() => _isLoading = false);
  }

  Future<void> _testLibrary() async {
    setState(() => _isLoading = true);
    _addDebugLine('📚 Testing library access...');
    
    try {
      final library = await ApiService.instance.getLibrary();
      _addDebugLine('✅ Library loaded: ${library.length} songs');
      
      for (int i = 0; i < library.length && i < 3; i++) {
        final song = library[i];
        _addDebugLine('  Song $i: ${song.title} by ${song.artist} (${song.spotifyId})');
      }
    } catch (e) {
      _addDebugLine('❌ Library test failed: $e');
    }
    
    setState(() => _isLoading = false);
  }

  Future<void> _testPlayFirstSong() async {
    setState(() => _isLoading = true);
    _addDebugLine('🎵 Testing play first song...');
    
    try {
      final library = await ApiService.instance.getLibrary();
      if (library.isEmpty) {
        _addDebugLine('❌ No songs in library to play');
        return;
      }
      
      final firstSong = library.first;
      _addDebugLine('🎵 Attempting to play: ${firstSong.title}');
      
      final audioPlayer = context.read<AudioPlayerService>();
      await audioPlayer.playSong(firstSong);
      
      _addDebugLine('✅ Play command completed - check debug console and audio player status');
    } catch (e) {
      _addDebugLine('❌ Play test failed: $e');
    }
    
    setState(() => _isLoading = false);
  }

  Future<void> _showQuickLogin() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const QuickLoginScreen()),
    );
    
    if (result == true) {
      _addDebugLine('✅ Login completed successfully');
    }
  }

  void _clearDebugOutput() {
    setState(() => _debugOutput = '');
  }
}
