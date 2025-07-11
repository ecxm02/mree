import 'package:flutter/material.dart';
import 'dart:ui';
import 'package:provider/provider.dart';
import '../../core/services/audio_player_service.dart';
import '../../core/services/api_service.dart';

class NowPlayingScreen extends StatelessWidget {
  const NowPlayingScreen({super.key});

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

    return FutureBuilder<String>(
      future: ApiService.instance.buildImageUrl(song.thumbnailUrl),
      builder: (context, snapshot) {
        final hasImage = snapshot.hasData && snapshot.data!.isNotEmpty;
        final imageUrl = hasImage ? snapshot.data! : '';

        return Scaffold(
          extendBodyBehindAppBar: true,
          appBar: AppBar(
            title: const Text('Now Playing'),
            backgroundColor: Colors.transparent,
            elevation: 0,
          ),
          body: Stack(
            fit: StackFit.expand,
            children: [
              // Background with blur
              if (hasImage)
                Container(
                  decoration: BoxDecoration(
                    image: DecorationImage(
                      image: NetworkImage(imageUrl),
                      fit: BoxFit.cover,
                    ),
                  ),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
                    child: Container(color: Colors.black.withValues(alpha: 0.6)),
                  ),
                ),

              // Content
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Album Art
                      Container(
                        width: 300,
                        height: 300,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: 0.3),
                              blurRadius: 20,
                              spreadRadius: 5,
                            ),
                          ],
                        ),
                        child:
                            hasImage
                                ? ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: Image.network(
                                    imageUrl,
                                    fit: BoxFit.cover,
                                  ),
                                )
                                : Container(
                                  decoration: BoxDecoration(
                                    color: Colors.grey[800],
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Center(
                                    child: Icon(
                                      Icons.music_note,
                                      size: 120,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ),
                      ),
                      const SizedBox(height: 32),

                      // Song Title and Artist
                      Text(
                        song.title,
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        song.artist,
                        style: const TextStyle(
                          fontSize: 18,
                          color: Colors.grey,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 32),

                      // Position Slider
                      SliderTheme(
                        data: SliderTheme.of(context).copyWith(
                          thumbColor: Theme.of(context).colorScheme.primary,
                          activeTrackColor:
                              Theme.of(context).colorScheme.primary,
                          inactiveTrackColor: Colors.grey.withValues(alpha: 0.3),
                          trackHeight: 4.0,
                        ),
                        child: Slider(
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
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              _formatDuration(player.position),
                              style: TextStyle(color: Colors.grey[400]),
                            ),
                            Text(
                              _formatDuration(player.duration),
                              style: TextStyle(color: Colors.grey[400]),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 32),

                      // Playback Controls
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          IconButton(
                            icon: const Icon(
                              Icons.skip_previous,
                              color: Colors.white,
                            ),
                            iconSize: 48,
                            onPressed: () {
                              // TODO: Implement previous track
                            },
                          ),
                          const SizedBox(width: 24),
                          Container(
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                            child: IconButton(
                              icon: Icon(
                                player.isPlaying
                                    ? Icons.pause
                                    : Icons.play_arrow,
                                color: Colors.white,
                              ),
                              iconSize: 48,
                              padding: const EdgeInsets.all(8),
                              onPressed: () {
                                player.togglePlayPause();
                              },
                            ),
                          ),
                          const SizedBox(width: 24),
                          IconButton(
                            icon: const Icon(
                              Icons.skip_next,
                              color: Colors.white,
                            ),
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
              ),
              // Show loading overlay when buffering
              if (player.isLoading)
                Container(
                  color: Colors.black54,
                  child: const Center(
                    child: CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation(Colors.white),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

String _formatDuration(Duration d) {
  final twoDigits = (int n) => n.toString().padLeft(2, '0');
  final minutes = twoDigits(d.inMinutes.remainder(60));
  final seconds = twoDigits(d.inSeconds.remainder(60));
  return '$minutes:$seconds';
}
