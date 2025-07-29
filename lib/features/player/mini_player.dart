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

    final Duration position = player.position;
    final Duration duration =
        song.duration != null
            ? Duration(seconds: song.duration!)
            : Duration.zero;
    final double progress =
        (duration.inMilliseconds > 0)
            ? (position.inMilliseconds / duration.inMilliseconds).clamp(
              0.0,
              1.0,
            )
            : 0.0;

    return GestureDetector(
      onTap: () => Navigator.of(context).pushNamed('/now-playing'),
      child: Container(
        height: 76,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHigh,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 4,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
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
                          style: TextStyle(
                            color: Colors.grey[400],
                            fontSize: 12,
                          ),
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
            Padding(
              padding: const EdgeInsets.only(left: 4, right: 4, top: 0),
              child: SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  trackHeight: 3,
                  thumbShape: const RoundSliderThumbShape(
                    enabledThumbRadius: 6,
                  ),
                  overlayShape: SliderComponentShape.noOverlay,
                  activeTrackColor: Colors.white,
                  inactiveTrackColor: Colors.grey[800],
                  thumbColor: Colors.white,
                ),
                child: Slider(
                  min: 0.0,
                  max: duration.inMilliseconds.toDouble().clamp(
                    1.0,
                    double.infinity,
                  ),
                  value:
                      position.inMilliseconds
                          .clamp(0, duration.inMilliseconds)
                          .toDouble(),
                  onChanged: (value) {
                    player.audioPlayer.seek(
                      Duration(milliseconds: value.round()),
                    );
                  },
                ),
              ),
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
