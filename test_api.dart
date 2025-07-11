import 'dart:io';
import 'dart:convert';

void main() async {
  // Test the backend API directly
  final serverUrl = 'http://100.67.83.60:8000';

  print('🔍 Testing backend API at: $serverUrl');

  try {
    // Test 1: Health check
    print('\n1. Testing health endpoint...');
    final healthClient = HttpClient();
    final healthRequest = await healthClient.getUrl(
      Uri.parse('$serverUrl/api/health/'),
    );
    final healthResponse = await healthRequest.close();
    final healthBody = await healthResponse.transform(utf8.decoder).join();
    print('Health check status: ${healthResponse.statusCode}');
    print('Health response: $healthBody');
    healthClient.close();

    // Test 2: Check if we can get library
    print('\n2. Testing library endpoint (should fail without auth)...');
    final libClient = HttpClient();
    final libRequest = await libClient.getUrl(
      Uri.parse('$serverUrl/api/search/library'),
    );
    final libResponse = await libRequest.close();
    final libBody = await libResponse.transform(utf8.decoder).join();
    print('Library status: ${libResponse.statusCode}');
    print('Library response: $libBody');
    libClient.close();

    // Test 3: Check streaming endpoint with a dummy spotify ID
    print('\n3. Testing streaming endpoint (should fail without auth)...');
    final streamClient = HttpClient();
    final streamRequest = await streamClient.getUrl(
      Uri.parse('$serverUrl/api/stream/play/dummy_spotify_id'),
    );
    final streamResponse = await streamRequest.close();
    final streamBody = await streamResponse.transform(utf8.decoder).join();
    print('Stream status: ${streamResponse.statusCode}');
    print('Stream response: $streamBody');
    streamClient.close();

    print('\n✅ API connectivity test completed!');
  } catch (e) {
    print('❌ Error testing API: $e');
  }
}
