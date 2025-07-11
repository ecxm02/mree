import 'package:just_audio/just_audio.dart';
import 'package:flutter/foundation.dart';
import '../models/song.dart';
import 'api_service.dart';
import 'server_config_service.dart';

class AudioPlayerService extends ChangeNotifier {
  static AudioPlayerService? _instance;
  static AudioPlayerService get instance =>
      _instance ??= AudioPlayerService._();

  final AudioPlayer _audioPlayer = AudioPlayer();
  Song? _currentSong;
  bool _isPlaying = false;
  bool _isLoading = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;

  AudioPlayerService._() {
    _setupAudioPlayer();
    // Ensure Dio base URL is initialized
    ApiService.instance.updateBaseUrl().catchError((e) {
      debugPrint('❌ Failed to update API base URL: $e');
    });
  }

  // Getters
  Song? get currentSong => _currentSong;
  bool get isPlaying => _isPlaying;
  bool get isLoading => _isLoading;
  Duration get position => _position;
  Duration get duration => _duration;
  AudioPlayer get audioPlayer => _audioPlayer;

  void _setupAudioPlayer() {
    // Listen to position changes
    _audioPlayer.positionStream.listen((position) {
      _position = position;
      notifyListeners();
    });

    // Listen to duration changes
    _audioPlayer.durationStream.listen((duration) {
      _duration = duration ?? Duration.zero;
      notifyListeners();
    });

    // Listen to playing state changes
    _audioPlayer.playingStream.listen((playing) {
      _isPlaying = playing;
      notifyListeners();
    });

    // Listen to processing state changes
    _audioPlayer.processingStateStream.listen((processingState) {
      _isLoading =
          processingState == ProcessingState.loading ||
          processingState == ProcessingState.buffering;
      notifyListeners();
    });

    // Listen to player state changes for debugging
    _audioPlayer.playerStateStream.listen((playerState) {
      debugPrint(
        'Player state: ${playerState.playing}, ${playerState.processingState}',
      );
    });

    // Listen for errors
    _audioPlayer.playbackEventStream.listen(
      (event) {
        // Log playback events for debugging
        debugPrint('🎵 Playback event: ${event.processingState}');
      },
      onError: (Object e, StackTrace stackTrace) {
        debugPrint('❌ A playback error occurred: $e');
        debugPrint('❌ Stack trace: $stackTrace');
        
        // Update loading state on error
        if (_isLoading) {
          _isLoading = false;
          notifyListeners();
        }
      },
    );
    
    // Listen for additional errors from the player itself
    _audioPlayer.processingStateStream.listen((state) {
      debugPrint('🎵 Processing state changed to: $state');
      if (state == ProcessingState.completed) {
        debugPrint('🎵 Playback completed');
      }
    });
  }

  /// Play a song by its Spotify ID
  Future<void> playSong(Song song) async {
    // Ensure base URL is up to date
    await ApiService.instance.updateBaseUrl();
    if (song.spotifyId == null) {
      throw Exception('Song has no Spotify ID');
    }

    try {
      _isLoading = true;
      _currentSong = song;
      notifyListeners();

      debugPrint('🎵 Starting to play song: ${song.title} by ${song.artist}');
      debugPrint('🎵 Spotify ID: ${song.spotifyId}');

      // APPROACH 1: Use API endpoint
      final streamUrl = await _buildStreamingUrl(song.spotifyId!);
      final headers = await _buildAuthHeaders();

      debugPrint('🌐 Trying API streaming URL: $streamUrl');
      debugPrint('🔐 Auth headers: ${headers.keys.join(', ')}');
      debugPrint('🔐 Has Authorization: ${headers.containsKey('Authorization')}');
