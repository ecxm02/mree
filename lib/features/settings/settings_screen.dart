import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/server_config_service.dart';
import '../../core/services/api_service.dart';
import '../auth/auth_provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String? _currentServerIp;
  String? _currentServerPort;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadCurrentSettings();
  }

  Future<void> _loadCurrentSettings() async {
    final ip = await ServerConfigService.instance.getServerIp();
    final port = await ServerConfigService.instance.getServerPort();

    setState(() {
      _currentServerIp = ip;
      _currentServerPort = port;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body:
          _isLoading
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Server Configuration Section
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Server Configuration',
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 16),

                          // Current server info
                          ListTile(
                            leading: const Icon(Icons.computer),
                            title: const Text('Server IP'),
                            subtitle: Text(
                              _currentServerIp ?? 'Not configured',
                            ),
                            contentPadding: EdgeInsets.zero,
                          ),
                          ListTile(
                            leading: const Icon(Icons.settings_ethernet),
                            title: const Text('Port'),
                            subtitle: Text(
                              _currentServerPort ?? 'Not configured',
                            ),
                            contentPadding: EdgeInsets.zero,
                          ),

                          const SizedBox(height: 16),

                          // Change server button
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton.icon(
                              onPressed: _showChangeServerDialog,
                              icon: const Icon(Icons.edit),
                              label: const Text('Change Server'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Account Section
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Account',
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 16),

                          // User info
                          Consumer<AuthProvider>(
                            builder: (context, authProvider, child) {
                              final user = authProvider.currentUser;
                              return Column(
                                children: [
                                  if (user != null) ...[
                                    ListTile(
                                      leading: const Icon(Icons.person),
                                      title: const Text('Username'),
                                      subtitle: Text(user.username),
                                      contentPadding: EdgeInsets.zero,
                                    ),
                                    ListTile(
                                      leading: const Icon(Icons.email),
                                      title: const Text('Email'),
                                      subtitle: Text(user.email),
                                      contentPadding: EdgeInsets.zero,
                                    ),
                                  ],

                                  const SizedBox(height: 16),

                                  // Logout button
                                  SizedBox(
                                    width: double.infinity,
                                    child: ElevatedButton.icon(
                                      onPressed: () => _handleLogout(context),
                                      icon: const Icon(Icons.logout),
                                      label: const Text('Logout'),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.red,
                                        foregroundColor: Colors.white,
                                      ),
                                    ),
                                  ),
                                ],
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // App Info Section
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'About',
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 16),

                          const ListTile(
                            leading: Icon(Icons.info),
                            title: Text('Version'),
                            subtitle: Text('1.0.0'),
                            contentPadding: EdgeInsets.zero,
                          ),
                          const ListTile(
                            leading: Icon(Icons.code),
                            title: Text('MREE'),
                            subtitle: Text('Music streaming made simple'),
                            contentPadding: EdgeInsets.zero,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
    );
  }

  void _showChangeServerDialog() {
    final ipController = TextEditingController(text: _currentServerIp ?? '');
    final portController = TextEditingController(
      text: _currentServerPort ?? '8000',
    );

    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Change Server'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: ipController,
                  decoration: const InputDecoration(
                    labelText: 'Server IP Address',
                    hintText: '192.168.1.100',
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: portController,
                  decoration: const InputDecoration(
                    labelText: 'Port',
                    hintText: '8000',
                  ),
                  keyboardType: TextInputType.number,
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed:
                    () => _updateServerConfig(
                      ipController.text,
                      portController.text,
                    ),
                child: const Text('Save'),
              ),
            ],
          ),
    );
  }

  Future<void> _updateServerConfig(String ip, String port) async {
    if (!ServerConfigService.instance.isValidIpAddress(ip)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter a valid IP address'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    try {
      await ServerConfigService.instance.setServerConfig(ip, port: port);
      await ApiService.instance.updateBaseUrl();

      // Test connection
      await ApiService.instance.getHealthStatus();

      setState(() {
        _currentServerIp = ip;
        _currentServerPort = port;
      });

      if (mounted) {
        Navigator.pop(context);

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Server configuration updated successfully'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to connect to server: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _handleLogout(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Logout'),
            content: const Text('Are you sure you want to logout?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Logout'),
              ),
            ],
          ),
    );

    if (confirmed == true && mounted) {
      await context.read<AuthProvider>().logout();
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
      }
    }
  }
}
