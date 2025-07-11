import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/audio_player_service.dart';
import '../../core/services/api_service.dart';

class NowPlayingScreen extends StatelessWidget {
  const NowPlayingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final player = context.watch<AudioPlayerService>();
    final song = player.currentSong;
    if (song == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Now Playing')),
        body: const Center(child: Text('No song is currently playing')),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Now Playing')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Album Art
            FutureBuilder<String>(
              future: ApiService.instance.buildImageUrl(song.thumbnailUrl),
              builder: (context, snapshot) {
                if (snapshot.hasData && snapshot.data!.isNotEmpty) {
                  return Image.network(
                    snapshot.data!,
                    height: 300,
                    fit: BoxFit.cover,
                  );
                }
                return const Icon(
                  Icons.music_note,
                  size: 200,
                  color: Colors.grey,
                );
              },
            ),
            const SizedBox(height: 24),
            // Song Title and Artist
            Text(
              song.title,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              song.artist,
              style: const TextStyle(fontSize: 18, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            // Position Slider
            Slider(
              min: 0,
              max: player.duration.inMilliseconds.toDouble(),
              value:
                  player.position.inMilliseconds
                      .clamp(0, player.duration.inMilliseconds)
                      .toDouble(),
              onChanged: (value) {
                player.seek(Duration(milliseconds: value.toInt()));
              },
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(_formatDuration(player.position)),
                  Text(_formatDuration(player.duration)),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // Playback Controls
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.skip_previous),
                  iconSize: 48,
                  onPressed: () {
                    // TODO: Implement previous track
                  },
                ),
                const SizedBox(width: 16),
                IconButton(
                  icon: Icon(
                    player.isPlaying
                        ? Icons.pause_circle_filled
                        : Icons.play_circle_filled,
                  ),
                  iconSize: 64,
                  onPressed: () {
                    player.togglePlayPause();
                  },
                ),
                const SizedBox(width: 16),
                IconButton(
                  icon: const Icon(Icons.skip_next),
                  iconSize: 48,
                  onPressed: () {
                    // TODO: Implement next track
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

String _formatDuration(Duration d) {
  final twoDigits = (int n) => n.toString().padLeft(2, '0');
  final minutes = twoDigits(d.inMinutes.remainder(60));
  final seconds = twoDigits(d.inSeconds.remainder(60));
  return '$minutes:$seconds';
}
