import 'dart:io';
import 'dart:convert';

void main() async {
  final baseUrl = 'http://100.67.83.60:8000';
  final client = HttpClient();

  try {
    print('Testing MREE Backend with Authentication...\n');

    // 1. Test Health Check (no auth required)
    print('1. Testing health endpoint...');
    final healthRequest = await client.getUrl(
      Uri.parse('$baseUrl/api/health/'),
    );
    final healthResponse = await healthRequest.close();
    final healthData = await healthResponse.transform(utf8.decoder).join();
    print('Health Status: ${healthResponse.statusCode}');
    print('Health Data: $healthData\n');

    // 2. Try to get library without auth (should fail)
    print('2. Testing library without auth (should fail)...');
    try {
      final libraryRequest = await client.getUrl(
        Uri.parse('$baseUrl/api/search/library'),
      );
      final libraryResponse = await libraryRequest.close();
      final libraryData = await libraryResponse.transform(utf8.decoder).join();
      print('Library Status: ${libraryResponse.statusCode}');
      print('Library Data: $libraryData\n');
    } catch (e) {
      print('Library without auth failed as expected: $e\n');
    }

    // 3. Login to get auth token
    print('3. Attempting login...');
    final loginRequest = await client.postUrl(
      Uri.parse('$baseUrl/api/auth/login'),
    );
    loginRequest.headers.set('Content-Type', 'application/json');

    // Try with test credentials - adjust these based on your backend
    final loginData = {
      'username': 'test', // Try common test username
      'password': 'password123', // Try common test password
    };

    loginRequest.add(utf8.encode(json.encode(loginData)));

    try {
      final loginResponse = await loginRequest.close();
      final loginResult = await loginResponse.transform(utf8.decoder).join();
      print('Login Status: ${loginResponse.statusCode}');
      print('Login Response: $loginResult');

      String? token;
      if (loginResponse.statusCode == 200) {
        final loginJson = json.decode(loginResult);
        token = loginJson['access_token'] ?? loginJson['token'];
        print('Auth token obtained: ${token?.substring(0, 20)}...\n');
      } else {
        print('Login failed, trying without auth for streaming test...\n');
      }

      // 4. Test library with auth (if we have a token)
      if (token != null) {
        print('4. Testing library with auth...');
        final authLibraryRequest = await client.getUrl(
          Uri.parse('$baseUrl/api/search/library'),
        );
        authLibraryRequest.headers.set('Authorization', 'Bearer $token');

        final authLibraryResponse = await authLibraryRequest.close();
        final authLibraryData =
            await authLibraryResponse.transform(utf8.decoder).join();
        print(
          'Authenticated Library Status: ${authLibraryResponse.statusCode}',
        );

        if (authLibraryResponse.statusCode == 200) {
          final libraryJson = json.decode(authLibraryData);
          if (libraryJson is List && libraryJson.isNotEmpty) {
            print('Found ${libraryJson.length} songs in library');
            final firstSong = libraryJson.first;
            print(
              'First song: ${firstSong['title']} by ${firstSong['artist']}',
            );
            print('Spotify ID: ${firstSong['spotify_id']}\n');

            // 5. Test streaming with a real song
            final spotifyId = firstSong['spotify_id'];
            if (spotifyId != null) {
              print('5. Testing streaming with auth for song: $spotifyId');
              final streamRequest = await client.getUrl(
                Uri.parse('$baseUrl/api/stream/play/$spotifyId'),
              );
              streamRequest.headers.set('Authorization', 'Bearer $token');

              final streamResponse = await streamRequest.close();
              print('Stream Status: ${streamResponse.statusCode}');
              print('Stream Headers: ${streamResponse.headers}');

              if (streamResponse.statusCode == 200) {
                print('✅ STREAMING SUCCESSFUL!');
                print('Content-Type: ${streamResponse.headers.contentType}');
                print(
                  'Content-Length: ${streamResponse.headers.contentLength}',
                );

                // Read first few bytes to verify it's audio data
                final firstChunk = await streamResponse.take(1024).toList();
                if (firstChunk.isNotEmpty) {
                  print('✅ Audio data received (${firstChunk.length} bytes)');
                } else {
                  print('⚠️ No audio data received');
                }
              } else {
                final streamData =
                    await streamResponse.transform(utf8.decoder).join();
                print('❌ Streaming failed: $streamData');
              }
            }
          } else {
            print('No songs found in library');
          }
        } else {
          print('Library request failed: $authLibraryData');
        }
      }
    } catch (e) {
      print('Login request failed: $e\n');
    }

    // 6. Test streaming without auth (should probably fail)
    print('\n6. Testing streaming without auth...');
    try {
      // Use a common Spotify ID for testing
      final testSpotifyId = '4iV5W9uYEdYUVa79Axb7Rh'; // Example Spotify ID
      final noAuthStreamRequest = await client.getUrl(
        Uri.parse('$baseUrl/api/stream/play/$testSpotifyId'),
      );

      final noAuthStreamResponse = await noAuthStreamRequest.close();
      final noAuthStreamData =
          await noAuthStreamResponse.transform(utf8.decoder).join();
      print('No-auth stream Status: ${noAuthStreamResponse.statusCode}');
      print('No-auth stream Data: $noAuthStreamData');
    } catch (e) {
      print('No-auth streaming failed as expected: $e');
    }
  } catch (e) {
    print('Test failed with error: $e');
  } finally {
    client.close();
  }
}
