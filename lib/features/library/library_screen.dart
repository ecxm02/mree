import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/services/api_service.dart';
import '../../core/models/song.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  List<Song> _songs = [];
  bool _isLoading = true;
  String _filterType = 'all';

  @override
  void initState() {
    super.initState();
    _loadLibrary();
  }

  Future<void> _loadLibrary() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final songs = await ApiService.instance.getLibrary();
      if (mounted) {
        setState(() {
          _songs = songs;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load library: ${e.toString()}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Library'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // Navigate to search screen - this is handled by main navigation
              // For now, just show a message
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Use bottom navigation to go to Search'),
                ),
              );
            },
          ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadLibrary),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadLibrary,
        child: Column(
          children: [
            // Filter chips
            _buildFilterChips(),

            // Quick access buttons
            _buildQuickAccessButtons(context),

            // Library content
            Expanded(
              child:
                  _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : _buildLibraryList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChips() {
    final filters = [
      {'key': 'all', 'label': 'All'},
      {'key': 'recently_added', 'label': 'Recently Added'},
      {'key': 'artists', 'label': 'Artists'},
      {'key': 'albums', 'label': 'Albums'},
    ];

    return Container(
      height: 60,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: filters.length,
        itemBuilder: (context, index) {
          final filter = filters[index];
          final isSelected = _filterType == filter['key'];

          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(filter['label'] as String),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  _filterType = filter['key'] as String;
                });
              },
              backgroundColor: Colors.grey[800],
              selectedColor: Theme.of(context).primaryColor,
            ),
          );
        },
      ),
    );
  }

  Widget _buildQuickAccessButtons(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          _buildQuickAccessItem(
            context,
            icon: Icons.download,
            title: 'Downloaded',
            subtitle: '${_songs.where((s) => s.canPlay).length} songs',
            onTap: () {
              setState(() {
                _filterType = 'all';
              });
            },
          ),
          _buildQuickAccessItem(
            context,
            icon: Icons.favorite,
            title: 'Popular Songs',
            subtitle: 'Most played',
            onTap: () async {
              try {
                final popularSongs =
                    await ApiService.instance.getPopularSongs();
                if (mounted) {
                  setState(() {
                    _songs = popularSongs;
                    _filterType = 'all';
                  });
                }
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      'Failed to load popular songs: ${e.toString()}',
                    ),
                  ),
                );
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAccessItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(vertical: 4),
      leading: Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.8),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Icon(icon, color: Colors.white, size: 24),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(
        subtitle,
        style: TextStyle(color: Colors.grey[400], fontSize: 12),
      ),
      trailing: const Icon(Icons.arrow_forward_ios, size: 16),
      onTap: onTap,
    );
  }

  Widget _buildLibraryList() {
    if (_songs.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.library_music_outlined,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              'Your library is empty',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              'Search and download songs to build your library',
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    // Filter songs based on selected filter
    List<Song> filteredSongs = _songs;
    switch (_filterType) {
      case 'recently_added':
        filteredSongs = List.from(_songs)..sort(
          (a, b) => (b.createdAt ?? DateTime.now()).compareTo(
            a.createdAt ?? DateTime.now(),
          ),
        );
        break;
      case 'artists':
        // Group by artists - for now just show all songs
        break;
      case 'albums':
        // Group by albums - for now just show all songs
        break;
      default:
        // Show all songs
        break;
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: filteredSongs.length,
      itemBuilder: (context, index) {
        final song = filteredSongs[index];
        return _buildSongTile(song);
      },
    );
  }

  Widget _buildSongTile(Song song) {
    return ListTile(
      leading: Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(4),
        ),
        child:
            song.thumbnailUrl != null
                ? ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: CachedNetworkImage(
                    imageUrl:
                        song.thumbnailUrl!.startsWith('http')
                            ? song.thumbnailUrl!
                            : '', // Will need to be handled differently for local images
                    fit: BoxFit.cover,
                    placeholder: (context, url) => const Icon(Icons.music_note),
                    errorWidget:
                        (context, url, error) => const Icon(Icons.music_note),
                  ),
                )
                : const Icon(Icons.music_note),
      ),
      title: Text(song.title, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(song.artist, maxLines: 1, overflow: TextOverflow.ellipsis),
          if (song.album != null)
            Text(
              song.album!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
        ],
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (song.duration != null)
            Text(song.durationText, style: TextStyle(color: Colors.grey[600])),
          const SizedBox(width: 8),
          if (song.canPlay)
            IconButton(
              icon: const Icon(Icons.play_arrow),
              onPressed: () => _playSong(song),
            )
          else if (song.isDownloading)
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            IconButton(
              icon: const Icon(Icons.more_vert),
              onPressed: () => _showSongOptions(song),
            ),
        ],
      ),
      onTap: () {
        if (song.canPlay) {
          _playSong(song);
        }
      },
    );
  }

  void _playSong(Song song) async {
    try {
      if (song.spotifyId != null) {
        await ApiService.instance.playSong(song.spotifyId!);
        await ApiService.instance.markSongAsPlayed(song.spotifyId!);
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Playing ${song.title}')));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to play song: ${e.toString()}')),
      );
    }
  }

  void _showSongOptions(Song song) {
    showModalBottomSheet(
      context: context,
      builder:
          (context) => Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.play_arrow),
                title: const Text('Play'),
                onTap: () {
                  Navigator.pop(context);
                  _playSong(song);
                },
              ),
              ListTile(
                leading: const Icon(Icons.playlist_add),
                title: const Text('Add to playlist'),
                onTap: () {
                  Navigator.pop(context);
                  // TODO: Implement add to playlist
                },
              ),
              ListTile(
                leading: const Icon(Icons.share),
                title: const Text('Share'),
                onTap: () {
                  Navigator.pop(context);
                  // TODO: Implement share
                },
              ),
              ListTile(
                leading: const Icon(Icons.delete),
                title: const Text('Remove from library'),
                onTap: () {
                  Navigator.pop(context);
                  // TODO: Implement remove from library
                },
              ),
            ],
          ),
    );
  }
}
