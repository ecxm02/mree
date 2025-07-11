import 'dart:convert';
import 'dart:io';

void main() async {
  final client = HttpClient();

  try {
    print('🔐 Testing with admin credentials...');

    // Step 1: Login with admin credentials
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

      // Step 2: Get library to find a song to stream
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
          // Find a downloaded song
          final downloadedSongs =
              library
                  .where(
                    (song) =>
                        song['download_status'] == 'completed' &&
                        song['spotify_id'] != null,
                  )
                  .toList();

          if (downloadedSongs.isNotEmpty) {
            final testSong = downloadedSongs.first;
            final spotifyId = testSong['spotify_id'];

            print(
              '\n🎵 Testing song: ${testSong['title']} by ${testSong['artist']}',
            );
            print('📁 File path: ${testSong['file_path']}');
            print('🆔 Spotify ID: $spotifyId');

            // Step 3: Test streaming endpoint
            print('\n🎵 Testing streaming endpoint...');
            request = await client.getUrl(
              Uri.parse('http://100.67.83.60:8000/api/stream/play/$spotifyId'),
            );
            request.headers.set('Authorization', 'Bearer $token');
            request.headers.set('Accept', 'audio/*');

            response = await request.close();

            print('📊 Response status: ${response.statusCode}');
            print('📊 Response headers: ${response.headers}');

            if (response.statusCode == 200) {
              print('✅ Streaming endpoint is working!');
              print('📊 Content-Type: ${response.headers.contentType}');
              print('📊 Content-Length: ${response.headers.contentLength}');

              // Read first few bytes to confirm it's audio data
              final bytes = await response.take(100).toList();
              final totalBytes = bytes.fold<int>(
                0,
                (sum, chunk) => sum + chunk.length,
              );
              print(
                '📊 First $totalBytes bytes received - this confirms audio data is being served',
              );
            } else {
              final errorBody = await response.transform(utf8.decoder).join();
              print('❌ Streaming failed: ${response.statusCode}');
              print('❌ Error: $errorBody');
            }

            // Step 4: Test direct file access via /music/ endpoint
            if (testSong['file_path'] != null) {
              final fileName = testSong['file_path'].toString().split('/').last;
              print('\n🎵 Testing direct file access...');
              print('📁 Filename: $fileName');

              request = await client.getUrl(
                Uri.parse('http://100.67.83.60:8000/music/$fileName'),
              );
              response = await request.close();

              print('📊 Direct file response status: ${response.statusCode}');

              if (response.statusCode == 200) {
                print('✅ Direct file access working!');
                final bytes = await response.take(100).toList();
                final totalBytes = bytes.fold<int>(
                  0,
                  (sum, chunk) => sum + chunk.length,
                );
                print(
                  '📊 First $totalBytes bytes received from direct file access',
                );
              } else {
                final errorBody = await response.transform(utf8.decoder).join();
                print('❌ Direct file access failed: ${response.statusCode}');
                print('❌ Error: $errorBody');
              }
            }
          } else {
            print('❌ No downloaded songs found in library');
            print(
              '📝 Available songs: ${library.map((s) => '${s['title']} (${s['download_status']})').join(', ')}',
            );
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
