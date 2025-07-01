// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'song.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Song _$SongFromJson(Map<String, dynamic> json) => Song(
  id: (json['id'] as num?)?.toInt(),
  title: json['title'] as String,
  artist: json['artist'] as String,
  album: json['album'] as String?,
  duration: (json['duration'] as num?)?.toInt(),
  spotifyId: json['spotify_id'] as String?,
  youtubeUrl: json['youtube_url'] as String?,
  filePath: json['file_path'] as String?,
  thumbnailUrl: json['thumbnail_url'] as String?,
  previewUrl: json['preview_url'] as String?,
  downloadStatus: json['download_status'] as String?,
  createdAt:
      json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
);

Map<String, dynamic> _$SongToJson(Song instance) => <String, dynamic>{
  'id': instance.id,
  'title': instance.title,
  'artist': instance.artist,
  'album': instance.album,
  'duration': instance.duration,
  'spotify_id': instance.spotifyId,
  'youtube_url': instance.youtubeUrl,
  'file_path': instance.filePath,
  'thumbnail_url': instance.thumbnailUrl,
  'preview_url': instance.previewUrl,
  'download_status': instance.downloadStatus,
  'created_at': instance.createdAt?.toIso8601String(),
};

SearchResponse _$SearchResponseFromJson(Map<String, dynamic> json) =>
    SearchResponse(
      results:
          (json['results'] as List<dynamic>)
              .map((e) => Song.fromJson(e as Map<String, dynamic>))
              .toList(),
      total: (json['total'] as num).toInt(),
    );

Map<String, dynamic> _$SearchResponseToJson(SearchResponse instance) =>
    <String, dynamic>{'results': instance.results, 'total': instance.total};

SearchRequest _$SearchRequestFromJson(Map<String, dynamic> json) =>
    SearchRequest(
      query: json['query'] as String,
      limit: (json['limit'] as num?)?.toInt() ?? 10,
    );

Map<String, dynamic> _$SearchRequestToJson(SearchRequest instance) =>
    <String, dynamic>{'query': instance.query, 'limit': instance.limit};

DownloadResponse _$DownloadResponseFromJson(Map<String, dynamic> json) =>
    DownloadResponse(
      message: json['message'] as String,
      spotifyId: json['spotify_id'] as String,
      status: json['status'] as String,
      taskId: json['task_id'] as String?,
      addedAt:
          json['added_at'] == null
              ? null
              : DateTime.parse(json['added_at'] as String),
    );

Map<String, dynamic> _$DownloadResponseToJson(DownloadResponse instance) =>
    <String, dynamic>{
      'message': instance.message,
      'spotify_id': instance.spotifyId,
      'status': instance.status,
      'task_id': instance.taskId,
      'added_at': instance.addedAt?.toIso8601String(),
    };
