import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/server_config_service.dart';
import '../../core/services/api_service.dart';
import '../../core/services/audio_player_service.dart';

class DebugInfoScreen extends StatefulWidget {
  const DebugInfoScreen({Key? key}) : super(key: key);

  @override
  State<DebugInfoScreen> createState() => _DebugInfoScreenState();
}

class _DebugInfoScreenState extends State<DebugInfoScreen> {
  String _serverIp = 'Not set';
  String _serverPort = 'Not set';
  String _serverUrl = 'Not set';
  String _apiBaseUrl = 'Not set';
  String _authToken = 'Not set';
  bool _isAuthenticated = false;

  @override
  void initState() {
    super.initState();
    _loadDebugInfo();
  }

  Future<void> _loadDebugInfo() async {
    final serverConfig = ServerConfigService.instance;
    final apiService = ApiService.instance;

    final ip = await serverConfig.getServerIp();
    final port = await serverConfig.getServerPort();
    final url = await serverConfig.getServerUrl();
    final apiUrl = await serverConfig.getApiBaseUrl();
    final token = await apiService.getStoredToken();
    final isAuth = await apiService.isAuthenticated();

    setState(() {
      _serverIp = ip ?? 'Not set';
      _serverPort = port;
      _serverUrl = url ?? 'Not set';
      _apiBaseUrl = apiUrl ?? 'Not set';
      _authToken =
          token != null ? 'Token exists (${token.length} chars)' : 'No token';
      _isAuthenticated = isAuth;
    });
  }

  Future<void> _testConnection() async {
    try {
      final response = await ApiService.instance.getHealthStatus();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ Connection successful: $response'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Connection failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Debug Info'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDebugInfo,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Server Configuration',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('Server IP: $_serverIp'),
                    Text('Server Port: $_serverPort'),
                    Text('Server URL: $_serverUrl'),
                    Text('API Base URL: $_apiBaseUrl'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Authentication',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('Is Authenticated: $_isAuthenticated'),
                    Text('Auth Token: $_authToken'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Audio Player Status',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Consumer<AudioPlayerService>(
                      builder: (context, player, child) {
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Current Song: ${player.currentSong?.title ?? 'None'}',
                            ),
                            Text('Is Playing: ${player.isPlaying}'),
                            Text('Is Loading: ${player.isLoading}'),
                            Text('Position: ${player.position}'),
                            Text('Duration: ${player.duration}'),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _testConnection,
                child: const Text('Test Connection'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
