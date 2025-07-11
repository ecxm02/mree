import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/audio_player_service.dart';
import '../../core/services/api_service.dart';
import '../../core/models/song.dart';

class MiniPlayer extends StatelessWidget {
  const MiniPlayer({super.key});

  @override
  Widget build(BuildContext context) {
    final player = context.watch<AudioPlayerService>();
    final song = player.currentSong;

    if (song == null) {
      return const SizedBox.shrink(); // No song playing, don't show mini player
    }

    return GestureDetector(
      onTap: () => Navigator.of(context).pushNamed('/now-playing'),
      child: Container(
        height: 60,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHigh,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 4,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: Row(
          children: [
            // Album Art
            _buildThumbnail(context, song),

            // Song Info
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      song.title,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      song.artist,
                      style: TextStyle(color: Colors.grey[400], fontSize: 12),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ),

            // Controls
            IconButton(
              icon: Icon(
                player.isPlaying ? Icons.pause : Icons.play_arrow,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => player.togglePlayPause(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildThumbnail(BuildContext context, Song song) {
    return Container(
      width: 60,
      height: 60,
      color: Colors.grey[800],
      child: FutureBuilder<String>(
        future: ApiService.instance.buildImageUrl(song.thumbnailUrl),
        builder: (context, snapshot) {
          if (snapshot.hasData && snapshot.data!.isNotEmpty) {
            return Image.network(snapshot.data!, fit: BoxFit.cover);
          }
          return const Center(
            child: Icon(Icons.music_note, color: Colors.grey),
          );
        },
      ),
    );
  }
}
