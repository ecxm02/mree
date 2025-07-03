import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import '../models/song.dart';
import 'server_config_service.dart';

class ApiService {
  late final Dio _dio;
  String? _currentBaseUrl;

  static ApiService? _instance;
  static ApiService get instance => _instance ??= ApiService._();

  ApiService._() {
    _initializeDio();
  }

  void _initializeDio() {
    _dio = Dio(
      BaseOptions(
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 10),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    // Add interceptor for auth token and dynamic base URL
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Set dynamic base URL if available
          if (_currentBaseUrl != null) {
            options.baseUrl = _currentBaseUrl!;
          } else {
            // Try to get from server config
            final apiBaseUrl =
                await ServerConfigService.instance.getApiBaseUrl();
            if (apiBaseUrl != null) {
              _currentBaseUrl = apiBaseUrl;
              options.baseUrl = apiBaseUrl;
            }
          }

          // Add auth token
          final token = await _getStoredToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            // Token expired, clear stored auth
            await clearAuth();
          }
          handler.next(error);
        },
      ),
    );
  }

  Future<void> updateBaseUrl() async {
    final apiBaseUrl = await ServerConfigService.instance.getApiBaseUrl();
    if (apiBaseUrl != null) {
      _currentBaseUrl = apiBaseUrl;
      _dio.options.baseUrl = apiBaseUrl;
    }
  }

  // Auth methods
  Future<AuthToken> login(LoginRequest request) async {
    final response = await _dio.post('/auth/login', data: request.toJson());
    final token = AuthToken.fromJson(response.data);
    await _storeToken(token.accessToken);
    return token;
  }

  Future<User> register(RegisterRequest request) async {
    final response = await _dio.post('/auth/register', data: request.toJson());
    return User.fromJson(response.data);
  }

  Future<User> getCurrentUser() async {
    final response = await _dio.get('/auth/me');
    return User.fromJson(response.data);
  }

  Future<void> logout() async {
    await clearAuth();
  }

  // Search methods
  Future<SearchResponse> searchSpotify(SearchRequest request) async {
    final response = await _dio.post('/search/spotify', data: request.toJson());
    return SearchResponse.fromJson(response.data);
  }

  Future<List<Song>> searchLocal(SearchRequest request) async {
    final response = await _dio.post('/search/local', data: request.toJson());
    return (response.data as List).map((json) => Song.fromJson(json)).toList();
  }

  Future<List<Song>> getLibrary() async {
    final response = await _dio.get('/search/library');
    return (response.data as List).map((json) => Song.fromJson(json)).toList();
  }

  Future<List<Song>> getPopularSongs() async {
    final response = await _dio.get('/search/popular');
    return (response.data as List).map((json) => Song.fromJson(json)).toList();
  }

  Future<List<Song>> getSongsByArtist(String artistName) async {
    final response = await _dio.get('/search/local/by-artist/$artistName');
    return (response.data as List).map((json) => Song.fromJson(json)).toList();
  }

  // Download methods
  Future<DownloadResponse> downloadSong(String spotifyId) async {
    final response = await _dio.post('/search/download/$spotifyId');
    return DownloadResponse.fromJson(response.data);
  }

  // Streaming methods
  Future<void> playSong(String spotifyId) async {
    await _dio.get('/stream/play/$spotifyId');
  }

  Future<void> markSongAsPlayed(String spotifyId) async {
    await _dio.post('/stream/mark-played/$spotifyId');
  }

  // Health check
  Future<Map<String, dynamic>> getHealthStatus() async {
    final response = await _dio.get('/health/');
    return response.data;
  }

  // Storage methods
  Future<String?> _getStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<void> _storeToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  Future<void> clearAuth() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  Future<bool> isAuthenticated() async {
    final token = await _getStoredToken();
    return token != null;
  }

  // Helper method to build full image URL
  Future<String> buildImageUrl(String? thumbnailUrl) async {
    if (thumbnailUrl == null) return '';
    if (thumbnailUrl.startsWith('http')) {
      return thumbnailUrl;
    }
    // Local image URL
    final serverUrl = await ServerConfigService.instance.getServerUrl();
    return serverUrl != null ? '$serverUrl$thumbnailUrl' : '';
  }

  // Helper method to build full music file URL
  Future<String> buildMusicUrl(String? filePath) async {
    if (filePath == null) return '';
    if (filePath.startsWith('http')) {
      return filePath;
    }
    // Local file URL
    final serverUrl = await ServerConfigService.instance.getServerUrl();
    return serverUrl != null
        ? '$serverUrl/music/${filePath.split('/').last}'
        : '';
  }
}
