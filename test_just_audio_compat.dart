import 'dart:convert';
import 'dart:io';

void main() async {
  final client = HttpClient();

  try {
    print('🔐 Testing Flutter app authentication flow...');

    // Step 1: Login with admin credentials (same as the app would do)
    var request = await client.postUrl(
      Uri.parse('http://100.67.83.60:8000/api/auth/login'),
    );
    request.headers.set('Content-Type', 'application/json');

    final loginData = {'username': 'admin', 'password': 'Admin123'};

    request.add(utf8.encode(jsonEncode(loginData)));
    var response = await request.close();

    if (response.statusCode == 200) {
      final responseBody = await response.transform(utf8.decoder).join();
      final loginResponse = jsonDecode(responseBody);
      final token = loginResponse['access_token'];

      print('✅ Login successful! Token: ${token.substring(0, 20)}...');

      // Step 2: Get library (to see what songs are available)
      print('\n📚 Getting library...');
      request = await client.getUrl(
        Uri.parse('http://100.67.83.60:8000/api/search/library'),
      );
      request.headers.set('Authorization', 'Bearer $token');
      response = await request.close();

      if (response.statusCode == 200) {
        final libraryBody = await response.transform(utf8.decoder).join();
        final library = jsonDecode(libraryBody) as List;

        print('✅ Library loaded: ${library.length} songs found');

        if (library.isNotEmpty) {
          final testSong = library.first;
          final spotifyId = testSong['spotify_id'];

          print(
            '\n🎵 Testing song: ${testSong['title']} by ${testSong['artist']}',
          );
          print('🆔 Spotify ID: $spotifyId');

          // Step 3: Test streaming with just_audio compatible headers
          print('\n🎵 Testing streaming with just_audio headers...');
          request = await client.getUrl(
            Uri.parse('http://100.67.83.60:8000/api/stream/play/$spotifyId'),
          );
          request.headers.set('Authorization', 'Bearer $token');
          request.headers.set('Accept', 'audio/*');

          // Add headers that just_audio might use
          request.headers.set('User-Agent', 'just_audio');
          request.headers.set(
            'Range',
            'bytes=0-',
          ); // just_audio often uses range requests

          response = await request.close();

          print('📊 Response status: ${response.statusCode}');
          print('📊 Response headers: ${response.headers}');

          if (response.statusCode == 200 || response.statusCode == 206) {
            print('✅ Streaming endpoint works with just_audio headers!');
            print('📊 Content-Type: ${response.headers.contentType}');
            print('📊 Content-Length: ${response.headers.contentLength}');

            // Test if we can read the stream like just_audio would
            final bytes = await response.take(1000).toList();
            final totalBytes = bytes.fold<int>(
              0,
              (sum, chunk) => sum + chunk.length,
            );
            print('📊 Successfully read $totalBytes bytes from stream');

            // Check if it's valid audio data
            if (bytes.isNotEmpty && bytes[0].isNotEmpty) {
              final firstBytes = bytes[0];
              if (firstBytes.length >= 3) {
                final header = String.fromCharCodes(firstBytes.take(3));
                if (header == 'ID3' || firstBytes[0] == 0xFF) {
                  print('✅ Valid MP3 audio data detected!');
                } else {
                  print(
                    '⚠️ Audio data format: ${firstBytes.take(10).toList()}',
                  );
                }
              }
            }

            // Step 4: Test if just_audio package can actually load this URL
            print('\n🎵 Testing URL format for just_audio compatibility...');
            final streamUrl =
                'http://100.67.83.60:8000/api/stream/play/$spotifyId';
            print('📎 Stream URL: $streamUrl');

            // Test if the URL is accessible without auth (should fail)
            print('\n🔒 Testing access without auth (should fail)...');
            request = await client.getUrl(Uri.parse(streamUrl));
            response = await request.close();
            print('📊 No-auth response: ${response.statusCode}');

            if (response.statusCode == 403) {
              print('✅ Authentication is properly enforced');
            } else {
              print('⚠️ Unexpected response without auth');
            }
          } else {
            final errorBody = await response.transform(utf8.decoder).join();
            print('❌ Streaming failed: ${response.statusCode}');
            print('❌ Error: $errorBody');
          }
        } else {
          print('❌ No songs in library');
        }
      } else {
        final errorBody = await response.transform(utf8.decoder).join();
        print('❌ Failed to get library: ${response.statusCode}');
        print('❌ Error: $errorBody');
      }
    } else {
      final errorBody = await response.transform(utf8.decoder).join();
      print('❌ Login failed: ${response.statusCode}');
      print('❌ Error: $errorBody');
    }
  } catch (e) {
    print('❌ Test failed with exception: $e');
  } finally {
    client.close();
  }
}
