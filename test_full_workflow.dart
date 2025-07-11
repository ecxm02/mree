import 'dart:io';
import 'dart:convert';

void main() async {
  final baseUrl = 'http://100.67.83.60:8000';
  final client = HttpClient();

  try {
    print('Testing MREE Backend - Register User and Test Streaming...\n');

    // 1. Test Health Check
    print('1. Testing health endpoint...');
    final healthRequest = await client.getUrl(
      Uri.parse('$baseUrl/api/health/'),
    );
    final healthResponse = await healthRequest.close();
    final healthData = await healthResponse.transform(utf8.decoder).join();
    print('Health Status: ${healthResponse.statusCode}');
    if (healthResponse.statusCode == 200) {
      final healthJson = json.decode(healthData);
      print('Backend Status: ${healthJson['status']}');
      print('Database: ${healthJson['checks']['database']['status']}');
    }
    print('');

    // 2. Register a test user
    print('2. Registering a test user...');
    final registerRequest = await client.postUrl(
      Uri.parse('$baseUrl/api/auth/register'),
    );
    registerRequest.headers.set('Content-Type', 'application/json');

    final registerData = {
      'username': 'testuser_${DateTime.now().millisecondsSinceEpoch}',
      'email': 'test_${DateTime.now().millisecondsSinceEpoch}@example.com',
      'password': 'TestPassword123',
      'display_name': 'Test User',
    };

    registerRequest.add(utf8.encode(json.encode(registerData)));

    final registerResponse = await registerRequest.close();
    final registerResult =
        await registerResponse.transform(utf8.decoder).join();
    print('Register Status: ${registerResponse.statusCode}');

    if (registerResponse.statusCode == 200) {
      final registerJson = json.decode(registerResult);
      print('✅ User registered successfully: ${registerJson['username']}');

      // 3. Login with the new user
      print('\n3. Logging in with new user...');
      final loginRequest = await client.postUrl(
        Uri.parse('$baseUrl/api/auth/login'),
      );
      loginRequest.headers.set('Content-Type', 'application/json');

      final loginData = {
        'username': registerData['username'],
        'password': registerData['password'],
      };

      loginRequest.add(utf8.encode(json.encode(loginData)));

      final loginResponse = await loginRequest.close();
      final loginResult = await loginResponse.transform(utf8.decoder).join();
      print('Login Status: ${loginResponse.statusCode}');

      if (loginResponse.statusCode == 200) {
        final loginJson = json.decode(loginResult);
        final token = loginJson['access_token'];
        print('✅ Login successful, token obtained');

        // 4. Get user library
        print('\n4. Getting user library...');
        final libraryRequest = await client.getUrl(
          Uri.parse('$baseUrl/api/search/library'),
        );
        libraryRequest.headers.set('Authorization', 'Bearer $token');

        final libraryResponse = await libraryRequest.close();
        final libraryData =
            await libraryResponse.transform(utf8.decoder).join();
        print('Library Status: ${libraryResponse.statusCode}');

        if (libraryResponse.statusCode == 200) {
          final libraryJson = json.decode(libraryData);
          print('✅ Library accessed successfully');
          print('Found ${libraryJson.length} songs in library');

          if (libraryJson.isNotEmpty) {
            final firstSong = libraryJson.first;
            print(
              'First song: ${firstSong['title']} by ${firstSong['artist']}',
            );
            final spotifyId = firstSong['spotify_id'];

            // 5. Test streaming with auth
            print('\n5. Testing streaming with auth for song: $spotifyId');
            final streamRequest = await client.getUrl(
              Uri.parse('$baseUrl/api/stream/play/$spotifyId'),
            );
            streamRequest.headers.set('Authorization', 'Bearer $token');

            final streamResponse = await streamRequest.close();
            print('Stream Status: ${streamResponse.statusCode}');

            if (streamResponse.statusCode == 200) {
              print('✅ STREAMING SUCCESSFUL!');
              print('Content-Type: ${streamResponse.headers.contentType}');
              print('Content-Length: ${streamResponse.headers.contentLength}');

              // Read first chunk to verify it's audio data
              final firstChunk = await streamResponse.take(1024).toList();
              if (firstChunk.isNotEmpty) {
                print('✅ Audio data received (${firstChunk.length} bytes)');

                // Check if it looks like audio data (common audio file headers)
                final bytes = firstChunk[0];
                if (bytes.length >= 3) {
                  final header = String.fromCharCodes(bytes.take(3));
                  if (header == 'ID3' || bytes[0] == 0xFF) {
                    print('✅ Looks like valid MP3 audio data');
                  } else {
                    print('⚠️ Data received but may not be audio format');
                  }
                }
              } else {
                print('⚠️ No audio data received');
              }
            } else {
              final streamData =
                  await streamResponse.transform(utf8.decoder).join();
              print('❌ Streaming failed: $streamData');
            }
          } else {
            print('ℹ️ Library is empty - no songs to test streaming with');

            // 6. Try a search to see if we can find any songs
            print('\n6. Searching for songs...');
            final searchRequest = await client.postUrl(
              Uri.parse('$baseUrl/api/search/spotify'),
            );
            searchRequest.headers.set('Authorization', 'Bearer $token');
            searchRequest.headers.set('Content-Type', 'application/json');

            final searchData = {'query': 'test song', 'limit': 5};

            searchRequest.add(utf8.encode(json.encode(searchData)));

            final searchResponse = await searchRequest.close();
            final searchResult =
                await searchResponse.transform(utf8.decoder).join();
            print('Search Status: ${searchResponse.statusCode}');

            if (searchResponse.statusCode == 200) {
              final searchJson = json.decode(searchResult);
              print('Search found ${searchJson['tracks']?.length ?? 0} tracks');

              if (searchJson['tracks']?.isNotEmpty == true) {
                final firstTrack = searchJson['tracks'][0];
                print(
                  'First result: ${firstTrack['name']} by ${firstTrack['artists']?[0]?['name']}',
                );

                // Try to download and then stream
                final spotifyId = firstTrack['id'];
                print('\n7. Trying to download song: $spotifyId');
                final downloadRequest = await client.postUrl(
                  Uri.parse('$baseUrl/api/search/download/$spotifyId'),
                );
                downloadRequest.headers.set('Authorization', 'Bearer $token');

                final downloadResponse = await downloadRequest.close();
                final downloadResult =
                    await downloadResponse.transform(utf8.decoder).join();
                print('Download Status: ${downloadResponse.statusCode}');

                if (downloadResponse.statusCode == 200) {
                  print('✅ Song downloaded successfully');

                  // Now try streaming the downloaded song
                  print('\n8. Trying to stream downloaded song...');
                  final streamDownloadedRequest = await client.getUrl(
                    Uri.parse('$baseUrl/api/stream/play/$spotifyId'),
                  );
                  streamDownloadedRequest.headers.set(
                    'Authorization',
                    'Bearer $token',
                  );

                  final streamDownloadedResponse =
                      await streamDownloadedRequest.close();
                  print(
                    'Stream Downloaded Status: ${streamDownloadedResponse.statusCode}',
                  );

                  if (streamDownloadedResponse.statusCode == 200) {
                    print('✅ STREAMING DOWNLOADED SONG SUCCESSFUL!');
                    final firstChunk =
                        await streamDownloadedResponse.take(1024).toList();
                    if (firstChunk.isNotEmpty) {
                      print(
                        '✅ Audio data received (${firstChunk.length} bytes)',
                      );
                    }
                  } else {
                    final streamDownloadedData =
                        await streamDownloadedResponse
                            .transform(utf8.decoder)
                            .join();
                    print(
                      '❌ Streaming downloaded song failed: $streamDownloadedData',
                    );
                  }
                } else {
                  print('❌ Download failed: $downloadResult');
                }
              }
            } else {
              print('❌ Search failed: $searchResult');
            }
          }
        } else {
          print('❌ Library access failed: $libraryData');
        }
      } else {
        print('❌ Login failed: $loginResult');
      }
    } else {
      print('❌ Registration failed: $registerResult');

      // Try with existing credentials if registration failed
      print('\n3. Trying login with potentially existing user...');
      final loginRequest = await client.postUrl(
        Uri.parse('$baseUrl/api/auth/login'),
      );
      loginRequest.headers.set('Content-Type', 'application/json');

      final loginData = {'username': 'admin', 'password': 'admin123'};

      loginRequest.add(utf8.encode(json.encode(loginData)));

      final loginResponse = await loginRequest.close();
      final loginResult = await loginResponse.transform(utf8.decoder).join();
      print('Admin Login Status: ${loginResponse.statusCode}');

      if (loginResponse.statusCode == 200) {
        print('✅ Admin login successful');
      } else {
        print('❌ Admin login failed: $loginResult');
      }
    }
  } catch (e) {
    print('Test failed with error: $e');
  } finally {
    client.close();
  }
}
