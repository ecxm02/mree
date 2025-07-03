import 'package:flutter/material.dart';
import '../../core/services/server_config_service.dart';
import '../../core/services/api_service.dart';
import '../../core/constants/app_constants.dart';

class ServerSetupScreen extends StatefulWidget {
  const ServerSetupScreen({super.key});

  @override
  State<ServerSetupScreen> createState() => _ServerSetupScreenState();
}

class _ServerSetupScreenState extends State<ServerSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _ipController = TextEditingController();
  final _portController = TextEditingController(text: AppConstants.defaultPort);
  final bool _isLoading = false;
  bool _isConnecting = false;

  @override
  void initState() {
    super.initState();
    _loadExistingConfig();
  }

  Future<void> _loadExistingConfig() async {
    final ip = await ServerConfigService.instance.getServerIp();
    final port = await ServerConfigService.instance.getServerPort();

    if (ip != null) {
      _ipController.text = ip;
    }
    _portController.text = port;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Logo/Title
                Icon(
                  Icons.settings_ethernet,
                  size: 80,
                  color: Theme.of(context).primaryColor,
                ),
                const SizedBox(height: 16),
                Text(
                  'Server Setup',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Enter your Raspberry Pi server details',
                  textAlign: TextAlign.center,
                  style: Theme.of(
                    context,
                  ).textTheme.bodyLarge?.copyWith(color: Colors.grey[600]),
                ),
                const SizedBox(height: 48),

                // IP Address field
                TextFormField(
                  controller: _ipController,
                  decoration: const InputDecoration(
                    labelText: 'Server IP Address',
                    hintText: '192.168.1.100',
                    prefixIcon: Icon(Icons.computer),
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter the server IP address';
                    }
                    if (!ServerConfigService.instance.isValidIpAddress(value)) {
                      return 'Please enter a valid IP address';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Port field
                TextFormField(
                  controller: _portController,
                  decoration: const InputDecoration(
                    labelText: 'Port',
                    hintText: AppConstants.defaultPortHint,
                    prefixIcon: Icon(Icons.settings_ethernet),
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter the port number';
                    }
                    final port = int.tryParse(value);
                    if (port == null || port < 1 || port > 65535) {
                      return 'Please enter a valid port number (1-65535)';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Connect button
                ElevatedButton(
                  onPressed:
                      _isLoading || _isConnecting ? null : _handleConnect,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child:
                      _isConnecting
                          ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                          : const Text('Connect to Server'),
                ),
                const SizedBox(height: 16),

                // Help text
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.blue.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: Colors.blue.withValues(alpha: 0.3),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.info, color: Colors.blue[300], size: 20),
                          const SizedBox(width: 8),
                          Text(
                            'Help',
                            style: TextStyle(
                              color: Colors.blue[300],
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Find your Raspberry Pi IP address:\n'
                        '• Check your router\'s admin panel\n'
                        '• Use "hostname -I" on the Pi\n'
                        '• Use network scanner apps\n'
                        '• Common format: ${AppConstants.defaultServerHint}',
                        style: TextStyle(color: Colors.blue[200], fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _handleConnect() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isConnecting = true;
    });

    try {
      final ip = _ipController.text.trim();
      final port = _portController.text.trim();

      // Save the server config
      await ServerConfigService.instance.setServerConfig(ip, port: port);

      // Update API service with new base URL
      await ApiService.instance.updateBaseUrl();

      // Test the connection
      final healthStatus = await ApiService.instance.getHealthStatus();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Connected successfully! Server status: ${healthStatus['status'] ?? 'OK'}',
            ),
            backgroundColor: Colors.green,
          ),
        );

        // Navigate to login screen
        Navigator.pushReplacementNamed(context, '/login');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Connection failed: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isConnecting = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _ipController.dispose();
    _portController.dispose();
    super.dispose();
  }
}
