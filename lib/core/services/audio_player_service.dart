import 'package:just_audio/just_audio.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';
import 'dart:convert';
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
    if (song.spotifyId == null) {
      throw Exception('Song has no Spotify ID');
    }

    try {
      debugPrint('🎵 Starting playSong for: ${song.title} by ${song.artist}');
      debugPrint('🆔 Spotify ID: ${song.spotifyId}');
      
      _isLoading = true;
      _currentSong = song;
      notifyListeners();

      final serverUrl = await ServerConfigService.instance.getServerUrl();
      debugPrint('🌐 Server URL: $serverUrl');
      if (serverUrl == null) throw Exception('Server URL not configured');

      final streamUrl = '$serverUrl/api/stream/play/${song.spotifyId!}';
      final headers = await _buildAuthHeaders();

      debugPrint('🌐 Full streaming URL: $streamUrl');
      debugPrint('🔐 Headers: $headers');

      // Test HTTP connectivity first
      debugPrint('🔍 Testing HTTP connectivity to endpoint...');
      await testStreamingEndpoint(song.spotifyId!);

      // First check if the URL is accessible
      debugPrint('🔍 Setting audio URL...');
      try {
        final loadedDuration = await _audioPlayer.setUrl(streamUrl, headers: headers);
        debugPrint('✅ URL set successfully, loaded duration: $loadedDuration');
        
        if (loadedDuration == null) {
          debugPrint('⚠️ Warning: Loaded duration is null, but URL was set');
        }
      } catch (setUrlError) {
        debugPrint('❌ Failed to set URL: $setUrlError');
        debugPrint('❌ Error type: ${setUrlError.runtimeType}');
        throw Exception('Failed to load audio stream: $setUrlError');
      }
      
      // Wait for the player to be ready
      debugPrint('🔍 Waiting for player to be ready...');
      await Future.delayed(const Duration(milliseconds: 500)); // Give some time for buffering
      
      // Check player state before playing
      final playerState = _audioPlayer.playerState;
      debugPrint('🎵 Player state before play: ${playerState.playing}, ${playerState.processingState}');
      
      // Start playback
      debugPrint('▶️ Starting playback...');
      try {
        await _audioPlayer.play();
        debugPrint('✅ Play command sent');
      } catch (playError) {
        debugPrint('❌ Failed to start playback: $playError');
        throw Exception('Failed to start playback: $playError');
      }
      
      // Check player state after playing
      await Future.delayed(const Duration(milliseconds: 200));
      final playerStateAfter = _audioPlayer.playerState;
      debugPrint('🎵 Player state after play: ${playerStateAfter.playing}, ${playerStateAfter.processingState}');

      // Mark as played in background
      try {
        debugPrint('📊 Marking song as played...');
        await ApiService.instance.markSongAsPlayed(song.spotifyId!);
        debugPrint('✅ Song marked as played');
      } catch (e) {
        debugPrint('⚠️ Failed to mark song as played: $e');
      }

      _isLoading = false;
      notifyListeners();
      debugPrint('🎵 playSong completed successfully');
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      debugPrint('❌ Playback error: $e');
      debugPrint('❌ Error type: ${e.runtimeType}');
      if (e is Exception) {
        debugPrint('❌ Exception details: ${e.toString()}');
      }
      throw Exception('Failed to play song: $e');
    }
  }

  Future<Map<String, String>> _buildAuthHeaders() async {
    final headers = <String, String>{
      'Accept': 'audio/*',
      'User-Agent': 'MREE-Flutter-App',
    };
    try {
      debugPrint('🔐 Building auth headers...');
      final token = await ApiService.instance.getStoredToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
        debugPrint('🔐 Auth token found and added to headers');
        debugPrint('🔐 Token preview: ${token.substring(0, 20)}...');
      } else {
        debugPrint('⚠️ Warning: No authentication token found');
        debugPrint('⚠️ This will likely cause a 401 Unauthorized error');
      }
    } catch (e) {
      debugPrint('❌ Error getting auth token: $e');
    }
    debugPrint('🔐 Final headers: $headers');
    return headers;
  }

  // Add debug and control methods
  /// Test connectivity by checking API health
  Future<void> testConnectivity() async {
    final status = await ApiService.instance.getHealthStatus();
    debugPrint('🔍 API Health status: $status');
  }

  /// Test HTTP connectivity to streaming endpoint
  Future<void> testStreamingEndpoint(String spotifyId) async {
    try {
      debugPrint('🔍 Testing HTTP connectivity to streaming endpoint...');
      
      final serverUrl = await ServerConfigService.instance.getServerUrl();
      if (serverUrl == null) {
        debugPrint('❌ Server URL not configured');
        return;
      }
      
      final streamUrl = '$serverUrl/api/stream/play/$spotifyId';
      debugPrint('🌐 Testing URL: $streamUrl');
      
      // Test with simple HTTP client first
      final client = HttpClient();
      try {
        final uri = Uri.parse(streamUrl);
        final request = await client.getUrl(uri);
        
        // Add headers
        final headers = await _buildAuthHeaders();
        headers.forEach((key, value) {
          request.headers.set(key, value);
        });
        
        final response = await request.close();
        debugPrint('✅ HTTP test successful!');
        debugPrint('📊 Status: ${response.statusCode}');
        debugPrint('📊 Headers: ${response.headers}');
        
        if (response.statusCode == 200) {
          // Read first few bytes
          final bytes = await response.take(100).toList();
          final totalBytes = bytes.fold<int>(0, (sum, chunk) => sum + chunk.length);
          debugPrint('📊 First $totalBytes bytes received');
        } else {
          final errorBody = await response.transform(utf8.decoder).join();
          debugPrint('❌ HTTP error response: $errorBody');
        }
        
      } catch (httpError) {
        debugPrint('❌ HTTP test failed: $httpError');
      } finally {
        client.close();
      }
    } catch (e) {
      debugPrint('❌ Test streaming endpoint error: $e');
    }
  }

  /// Check if a given [song] is the current song
  bool isCurrentSong(Song song) {
    return _currentSong?.spotifyId == song.spotifyId;
  }

  /// Check if a given [song] is currently playing
  bool isSongPlaying(Song song) {
    return isCurrentSong(song) && _isPlaying;
  }

  /// Pause playback
  Future<void> pause() async {
    await _audioPlayer.pause();
  }

  /// Resume playback
  Future<void> resume() async {
    await _audioPlayer.play();
  }

  /// Toggle play/pause state
  Future<void> togglePlayPause() async {
    if (_isPlaying) {
      await pause();
    } else {
      await resume();
    }
  }

  /// Seek to a specific [position]
  Future<void> seek(Duration position) async {
    await _audioPlayer.seek(position);
  }
}
