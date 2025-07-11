import 'package:just_audio/just_audio.dart';

/// A service to help debug audio playback issues
class AudioDebugService {
  static AudioDebugService? _instance;
  static AudioDebugService get instance => _instance ??= AudioDebugService._();

  AudioDebugService._();

  /// Check if the given URL is accessible by attempting to load its headers
  /// Returns the status code, headers, or error message
  Future<Map<String, dynamic>> checkAudioUrl(
    String url,
    Map<String, String> headers,
  ) async {
    try {
      // Create an audio player for testing
      final AudioPlayer testPlayer = AudioPlayer();

      try {
        // Try to set the audio source
        await testPlayer.setUrl(url, headers: headers);

        // If successful, get duration
        final duration = await testPlayer.duration;

        // Clean up
        await testPlayer.dispose();

        return {
          'success': true,
          'duration': duration?.inSeconds ?? 0,
          'message': 'URL is accessible and audio is valid',
        };
      } catch (e) {
        // Cleanup
        await testPlayer.dispose();

        return {
          'success': false,
          'error': e.toString(),
          'message': 'Failed to set audio source',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'error': e.toString(),
        'message': 'Error checking audio URL',
      };
    }
  }
}
