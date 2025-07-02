import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/services/api_service.dart';
import '../../core/models/user.dart';

class AuthProvider extends ChangeNotifier {
  String? _token;
  User? _currentUser;
  bool _isLoading = false;

  String? get token => _token;
  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _token != null;

  AuthProvider() {
    _loadStoredAuth();
  }

  Future<void> _loadStoredAuth() async {
    _isLoading = true;
    notifyListeners();

    try {
      final isAuth = await ApiService.instance.isAuthenticated();
      if (isAuth) {
        // Try to get current user to validate token
        _currentUser = await ApiService.instance.getCurrentUser();
        _token = await _getStoredToken();
      }
    } catch (e) {
      // Token might be expired, clear it
      await clearAuth();
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> setToken(String token) async {
    _token = token;
    await _storeToken(token);

    try {
      _currentUser = await ApiService.instance.getCurrentUser();
    } catch (e) {
      // If getting user fails, clear auth
      await clearAuth();
      rethrow;
    }

    notifyListeners();
  }

  Future<void> clearAuth() async {
    _token = null;
    _currentUser = null;
    await ApiService.instance.clearAuth();
    notifyListeners();
  }

  Future<void> logout() async {
    await clearAuth();
  }

  Future<String?> _getStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<void> _storeToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }
}
