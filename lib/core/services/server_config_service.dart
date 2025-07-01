import 'package:shared_preferences/shared_preferences.dart';

class ServerConfigService {
  static const String _serverIpKey = 'server_ip';
  static const String _serverPortKey = 'server_port';
  static const String _defaultPort = '8000';

  static ServerConfigService? _instance;
  static ServerConfigService get instance =>
      _instance ??= ServerConfigService._();

  ServerConfigService._();

  Future<String?> getServerIp() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_serverIpKey);
  }

  Future<String> getServerPort() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_serverPortKey) ?? _defaultPort;
  }

  Future<String?> getServerUrl() async {
    final ip = await getServerIp();
    if (ip == null) return null;

    final port = await getServerPort();
    return 'http://$ip:$port';
  }

  Future<String?> getApiBaseUrl() async {
    final serverUrl = await getServerUrl();
    if (serverUrl == null) return null;

    return '$serverUrl/api';
  }

  Future<void> setServerConfig(String ip, {String? port}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_serverIpKey, ip);
    if (port != null) {
      await prefs.setString(_serverPortKey, port);
    }
  }

  Future<void> clearServerConfig() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_serverIpKey);
    await prefs.remove(_serverPortKey);
  }

  Future<bool> hasServerConfig() async {
    final ip = await getServerIp();
    return ip != null && ip.isNotEmpty;
  }

  bool isValidIpAddress(String ip) {
    // Basic IP validation
    final ipRegex = RegExp(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$');
    if (!ipRegex.hasMatch(ip)) return false;

    final parts = ip.split('.');
    for (final part in parts) {
      final num = int.tryParse(part);
      if (num == null || num < 0 || num > 255) return false;
    }
    return true;
  }
}
