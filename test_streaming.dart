import 'dart:io';
import 'dart:convert';

void main() async {
  // Test the streaming workflow that your Flutter app would follow
  final serverUrl = 'http://100.67.83.60:8000';

  print('🎵 Testing music streaming workflow...');

  try {
    // Step 1: Test login (you'll need to provide real credentials)
    print('\n1. Testing login...');

    // Create a test login request
    final loginData = {
      'username': 'your_username', // Replace with actual username
      'password': 'your_password', // Replace with actual password
    };

    final client = HttpClient();

    // Login request
    final loginRequest = await client.postUrl(
      Uri.parse('$serverUrl/api/auth/login'),
    );
    loginRequest.headers.contentType = ContentType.json;
    loginRequest.write(jsonEncode(loginData));

    final loginResponse = await loginRequest.close();
    final loginBody = await loginResponse.transform(utf8.decoder).join();

    print('Login status: ${loginResponse.statusCode}');

    if (loginResponse.statusCode != 200) {
      print('❌ Login failed: $loginBody');
      print('💡 You need to update the username/password in the test script');
      client.close();
      return;
    }

    final loginJson = jsonDecode(loginBody);
    final token = loginJson['access_token'];
    print('✅ Login successful, got token: ${token.substring(0, 20)}...');

    // Step 2: Get library to find a song to test
    print('\n2. Getting library...');
    final libRequest = await client.getUrl(
      Uri.parse('$serverUrl/api/search/library'),
    );
    libRequest.headers.set('Authorization', 'Bearer $token');

    final libResponse = await libRequest.close();
    final libBody = await libResponse.transform(utf8.decoder).join();

    print('Library status: ${libResponse.statusCode}');

    if (libResponse.statusCode != 200) {
      print('❌ Library failed: $libBody');
      client.close();
      return;
    }

    final library = jsonDecode(libBody) as List;
    print('📚 Found ${library.length} songs in library');

    if (library.isEmpty) {
      print('❌ No songs in library to test with');
      client.close();
      return;
    }

    // Find a song that can be played
    Map<String, dynamic>? testSong;
    for (final song in library) {
      if (song['download_status'] == 'completed' &&
          song['spotify_id'] != null) {
        testSong = song;
        break;
      }
    }

    if (testSong == null) {
      print('❌ No completed songs found in library');
      client.close();
      return;
    }

    print(
      '🎵 Testing with song: "${testSong['title']}" by ${testSong['artist']}',
    );

    // Step 3: Test streaming endpoint
    print('\n3. Testing streaming...');
    final spotifyId = testSong['spotify_id'];
    final streamRequest = await client.getUrl(
      Uri.parse('$serverUrl/api/stream/play/$spotifyId'),
    );
    streamRequest.headers.set('Authorization', 'Bearer $token');
    streamRequest.headers.set('Accept', 'audio/*');

    final streamResponse = await streamRequest.close();

    print('Stream status: ${streamResponse.statusCode}');
    print('Content-Type: ${streamResponse.headers.contentType}');
    print('Content-Length: ${streamResponse.headers.contentLength}');

    if (streamResponse.statusCode == 200) {
      print('✅ Streaming endpoint is working!');
      print('🎧 Audio content is being served properly');

      // Read a small portion to verify it's audio content
      final firstBytes = <int>[];
      await for (final chunk in streamResponse.take(10)) {
        firstBytes.addAll(chunk);
        if (firstBytes.length >= 100) break;
      }

      print(
        '📊 First few bytes: ${firstBytes.take(20).map((b) => b.toRadixString(16).padLeft(2, '0')).join(' ')}',
      );

      // Check if it looks like an MP3 file (starts with ID3 or FF)
      if (firstBytes.length >= 3) {
        if ((firstBytes[0] == 0x49 &&
                firstBytes[1] == 0x44 &&
                firstBytes[2] == 0x33) || // ID3
            (firstBytes[0] == 0xFF && (firstBytes[1] & 0xE0) == 0xE0)) {
          // MP3 sync word
          print('✅ Content appears to be valid MP3 audio');
        } else {
          print('⚠️  Content may not be valid MP3 (unexpected header)');
        }
      }
    } else {
      final errorBody = await streamResponse.transform(utf8.decoder).join();
      print('❌ Streaming failed: $errorBody');
    }

    client.close();
  } catch (e) {
    print('❌ Error: $e');
  }
}
