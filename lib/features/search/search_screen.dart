import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/services/api_service.dart';
import '../../core/models/song.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  bool _isSearching = false;
  bool _isLoading = false;
  bool _searchingSpotify = false;
  List<Song> _localResults = [];
  SearchResponse? _spotifyResults;
  String _currentQuery = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Search')),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'What do you want to listen to?',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon:
                        _searchController.text.isNotEmpty
                            ? IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () {
                                setState(() {
                                  _searchController.clear();
                                  _isSearching = false;
                                  _localResults = [];
                                  _spotifyResults = null;
                                  _currentQuery = '';
                                });
                              },
                            )
                            : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: BorderSide.none,
                    ),
                    filled: true,
                    fillColor:
                        Theme.of(context).colorScheme.surfaceContainerHighest,
                  ),
                  onChanged: (value) {
                    setState(() {
                      _isSearching = value.isNotEmpty;
                      if (value.isNotEmpty) {
                        _performLocalSearch(value);
                      } else {
                        _localResults = [];
                        _spotifyResults = null;
                        _currentQuery = '';
                      }
                    });
                  },
                ),
                if (_isSearching && _currentQuery.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed:
                          _searchingSpotify
                              ? null
                              : () => _performSpotifySearch(_currentQuery),
                      icon:
                          _searchingSpotify
                              ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                              : const Icon(Icons.cloud_download),
                      label: Text(
                        _searchingSpotify
                            ? 'Searching Spotify...'
                            : 'Search Spotify',
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),

          // Content area
          Expanded(
            child:
                _isSearching ? _buildSearchResults() : _buildBrowseCategories(),
          ),
        ],
      ),
    );
  }

  void _performLocalSearch(String query) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _isLoading = true;
      _currentQuery = query.trim();
    });

    try {
      final searchRequest = SearchRequest(query: query.trim());
      final results = await ApiService.instance.searchLocal(searchRequest);

      if (mounted) {
        setState(() {
          _localResults = results;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _localResults = [];
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Search failed: ${e.toString()}')),
        );
      }
    }
  }

  void _performSpotifySearch(String query) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _searchingSpotify = true;
    });

    try {
      final searchRequest = SearchRequest(query: query.trim());
      final results = await ApiService.instance.searchSpotify(searchRequest);

      if (mounted) {
        setState(() {
          _spotifyResults = results;
          _searchingSpotify = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _spotifyResults = null;
          _searchingSpotify = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Spotify search failed: ${e.toString()}')),
        );
      }
    }
  }

  void _downloadSpotifySong(String spotifyId) async {
    try {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Starting download...')));

      final response = await ApiService.instance.downloadSong(spotifyId);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message),
            backgroundColor:
                response.status == 'queued' ? Colors.green : Colors.orange,
          ),
        );

        // Refresh local search if download was queued
        if (response.status == 'queued' && _currentQuery.isNotEmpty) {
          _performLocalSearch(_currentQuery);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Download failed: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Widget _buildSearchResults() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Local results section
          if (_localResults.isNotEmpty) ...[
            Text(
              'From Your Library',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _localResults.length,
              itemBuilder: (context, index) {
                final song = _localResults[index];
                return _buildSongTile(song, isLocal: true);
              },
            ),
            const SizedBox(height: 24),
          ],

          // Spotify results section
          if (_spotifyResults != null &&
              _spotifyResults!.results.isNotEmpty) ...[
            Text(
              'From Spotify (${_spotifyResults!.total} results)',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _spotifyResults!.results.length,
              itemBuilder: (context, index) {
                final song = _spotifyResults!.results[index];
                return _buildSongTile(song, isLocal: false);
              },
            ),
          ],

          // No results message
          if (_localResults.isEmpty &&
              (_spotifyResults == null ||
                  _spotifyResults!.results.isEmpty)) ...[
            const SizedBox(height: 48),
            Center(
              child: Column(
                children: [
                  Icon(Icons.search_off, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    'No results found',
                    style: Theme.of(
                      context,
                    ).textTheme.titleMedium?.copyWith(color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Try searching on Spotify for more songs',
                    style: Theme.of(
                      context,
                    ).textTheme.bodyMedium?.copyWith(color: Colors.grey[500]),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSongTile(Song song, {required bool isLocal}) {
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
                  child: FutureBuilder<String>(
                    future: ApiService.instance.buildImageUrl(
                      song.thumbnailUrl,
                    ),
                    builder: (context, snapshot) {
                      if (snapshot.hasData && snapshot.data!.isNotEmpty) {
                        return CachedNetworkImage(
                          imageUrl: snapshot.data!,
                          fit: BoxFit.cover,
                          placeholder:
                              (context, url) => const Icon(Icons.music_note),
                          errorWidget:
                              (context, url, error) =>
                                  const Icon(Icons.music_note),
                        );
                      }
                      return const Icon(Icons.music_note);
                    },
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
          if (isLocal && song.canPlay)
            IconButton(
              icon: const Icon(Icons.play_arrow),
              onPressed: () => _playSong(song),
            )
          else if (isLocal && song.isDownloading)
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else if (!isLocal)
            IconButton(
              icon: const Icon(Icons.download),
              onPressed:
                  song.spotifyId != null
                      ? () => _downloadSpotifySong(song.spotifyId!)
                      : null,
            )
          else
            IconButton(
              icon: const Icon(Icons.more_vert),
              onPressed: () => _showSongOptions(song),
            ),
        ],
      ),
      onTap: () {
        if (isLocal && song.canPlay) {
          _playSong(song);
        } else if (!isLocal && song.spotifyId != null) {
          _downloadSpotifySong(song.spotifyId!);
        }
      },
    );
  }

  void _playSong(Song song) async {
    try {
      if (song.spotifyId != null) {
        await ApiService.instance.playSong(song.spotifyId!);
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('Playing ${song.title}')));
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to play song: ${e.toString()}')),
        );
      }
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
              if (song.spotifyId != null)
                ListTile(
                  leading: const Icon(Icons.open_in_new),
                  title: const Text('Open in Spotify'),
                  onTap: () {
                    Navigator.pop(context);
                    // TODO: Implement open in Spotify
                  },
                ),
            ],
          ),
    );
  }

  Widget _buildBrowseCategories() {
    final categories = [
      {'name': 'Made For You', 'color': Colors.purple},
      {'name': 'Recently Played', 'color': Colors.green},
      {'name': 'Liked Songs', 'color': Colors.red},
      {'name': 'Albums', 'color': Colors.blue},
      {'name': 'Artists', 'color': Colors.orange},
      {'name': 'Podcasts', 'color': Colors.teal},
    ];

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
        childAspectRatio: 1.5,
      ),
      itemCount: categories.length,
      itemBuilder: (context, index) {
        final category = categories[index];
        return Container(
          decoration: BoxDecoration(
            color: category['color'] as Color,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Stack(
            children: [
              Positioned(
                bottom: 8,
                left: 16,
                child: Text(
                  category['name'] as String,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Positioned(
                top: -20,
                right: -20,
                child: Transform.rotate(
                  angle: 0.3,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: const BoxDecoration(
                      color: Colors.black12,
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    child: const Icon(
                      Icons.music_note,
                      color: Colors.white54,
                      size: 40,
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
