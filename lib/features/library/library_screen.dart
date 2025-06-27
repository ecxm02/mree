import 'package:flutter/material.dart';

class LibraryScreen extends StatelessWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Library'),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
          IconButton(icon: const Icon(Icons.sort), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          // Filter chips
          _buildFilterChips(),

          // Quick access buttons
          _buildQuickAccessButtons(context),

          // Library content
          Expanded(child: _buildLibraryList()),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    return Container(
      height: 60,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Chip(
            label: const Text('Recently Added'),
            backgroundColor: Colors.grey[800],
          ),
          const SizedBox(width: 8),
          Chip(label: const Text('Artists'), backgroundColor: Colors.grey[800]),
          const SizedBox(width: 8),
          Chip(label: const Text('Albums'), backgroundColor: Colors.grey[800]),
        ],
      ),
    );
  }

  Widget _buildQuickAccessButtons(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          _buildLibraryItem(
            context,
            icon: Icons.download,
            title: 'Downloaded',
            subtitle: '3 songs',
            isSpecial: true,
          ),
          _buildLibraryItem(
            context,
            icon: Icons.favorite,
            title: 'Liked Songs',
            subtitle: '142 songs',
            isSpecial: true,
          ),
        ],
      ),
    );
  }

  Widget _buildLibraryList() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: 15,
      itemBuilder: (context, index) {
        if (index % 3 == 0) {
          return _buildLibraryItem(
            context,
            icon: Icons.queue_music,
            title: 'My Playlist ${index ~/ 3 + 1}',
            subtitle: '${20 + index * 3} songs',
          );
        } else if (index % 3 == 1) {
          return _buildLibraryItem(
            context,
            icon: Icons.album,
            title: 'Album ${index ~/ 3 + 1}',
            subtitle: 'Artist Name',
          );
        } else {
          return _buildLibraryItem(
            context,
            icon: Icons.person,
            title: 'Artist ${index ~/ 3 + 1}',
            subtitle: 'Following',
          );
        }
      },
    );
  }

  Widget _buildLibraryItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    bool isSpecial = false,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(vertical: 4),
      leading: Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color:
              isSpecial
                  ? Theme.of(context).colorScheme.primary.withValues(alpha: 0.8)
                  : Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(isSpecial ? 4 : 28),
        ),
        child: Icon(
          icon,
          color: isSpecial ? Colors.white : Colors.grey[400],
          size: isSpecial ? 24 : 20,
        ),
      ),
      title: Text(
        title,
        style: TextStyle(
          fontWeight: isSpecial ? FontWeight.w600 : FontWeight.normal,
        ),
      ),
      subtitle: Text(
        subtitle,
        style: TextStyle(color: Colors.grey[400], fontSize: 12),
      ),
      trailing: IconButton(icon: const Icon(Icons.more_vert), onPressed: () {}),
      onTap: () {
        // Handle library item selection
      },
    );
  }
}
