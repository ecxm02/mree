import 'package:json_annotation/json_annotation.dart';

part 'song.g.dart';

@JsonSerializable()
class Song {
  final int? id;
  final String title;
  final String artist;
  final String? album;
  final int? duration;
  @JsonKey(name: 'spotify_id')
  final String? spotifyId;
  @JsonKey(name: 'youtube_url')
  final String? youtubeUrl;
  @JsonKey(name: 'file_path')
  final String? filePath;
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @JsonKey(name: 'preview_url')
  final String? previewUrl;
  @JsonKey(name: 'download_status')
  final String? downloadStatus;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;

  const Song({
    this.id,
    required this.title,
    required this.artist,
    this.album,
    this.duration,
    this.spotifyId,
    this.youtubeUrl,
    this.filePath,
    this.thumbnailUrl,
    this.previewUrl,
    this.downloadStatus,
    this.createdAt,
  });

  factory Song.fromJson(Map<String, dynamic> json) => _$SongFromJson(json);
  Map<String, dynamic> toJson() => _$SongToJson(this);

  String get durationText {
    if (duration == null) return '';
    final minutes = duration! ~/ 60;
    final seconds = duration! % 60;
    return '${minutes}:${seconds.toString().padLeft(2, '0')}';
  }

  bool get isDownloaded => downloadStatus == 'completed';
  bool get isDownloading => downloadStatus == 'downloading';
  bool get canPlay => filePath != null && isDownloaded;
}

@JsonSerializable()
class SearchResponse {
  final List<Song> results;
  final int total;

  const SearchResponse({required this.results, required this.total});

  factory SearchResponse.fromJson(Map<String, dynamic> json) =>
      _$SearchResponseFromJson(json);
  Map<String, dynamic> toJson() => _$SearchResponseToJson(this);
}

@JsonSerializable()
class SearchRequest {
  final String query;
  final int limit;

  const SearchRequest({required this.query, this.limit = 10});

  factory SearchRequest.fromJson(Map<String, dynamic> json) =>
      _$SearchRequestFromJson(json);
  Map<String, dynamic> toJson() => _$SearchRequestToJson(this);
}

@JsonSerializable()
class DownloadResponse {
  final String message;
  @JsonKey(name: 'spotify_id')
  final String spotifyId;
  final String status;
  @JsonKey(name: 'task_id')
  final String? taskId;
  @JsonKey(name: 'added_at')
  final DateTime? addedAt;

  const DownloadResponse({
    required this.message,
    required this.spotifyId,
    required this.status,
    this.taskId,
    this.addedAt,
  });

  factory DownloadResponse.fromJson(Map<String, dynamic> json) =>
      _$DownloadResponseFromJson(json);
  Map<String, dynamic> toJson() => _$DownloadResponseToJson(this);
}
