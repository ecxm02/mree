#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "Elasticsearch Pinyin Reindexing Script (Linux)"
echo "============================================================"

# Ensure we are in backend directory
if [ ! -f "app/services/elasticsearch_service.py" ]; then
  echo "❌ Please run this script from the backend directory" 1>&2
  echo "Current directory: $(pwd)" 1>&2
  exit 1
fi

# Required files
for f in songs_pinyin_mapping.json reindex_with_pinyin.py app/services/elasticsearch_service.py; do
  if [ ! -f "$f" ]; then
    echo "❌ Required file missing: $f" 1>&2
    exit 1
  fi
done
echo "✅ All required files found"

# Check Elasticsearch (host port 9201 per docker-compose)
echo "🔍 Checking Elasticsearch connection..."
if ! curl -fsS http://localhost:9201/_cluster/health >/dev/null; then
  echo "❌ Cannot connect to Elasticsearch at http://localhost:9201" 1>&2
  echo "   Make sure docker-compose is running: docker-compose up -d music-search" 1>&2
  exit 1
fi
echo "✅ Elasticsearch is running"

# Run reindex with local override for host execution
echo "🚀 Starting reindexing process..."
ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9201}" \
python3 reindex_with_pinyin.py || exit_code=$?

if [ "${exit_code:-0}" -eq 0 ]; then
  echo "\n🎉 Reindexing completed successfully!"
  echo "🔍 Your Elasticsearch now supports pinyin search!"
  echo "   Try searching for 'dao gao' to find Chinese songs like '祷告'"
else
  echo "\n💥 Reindexing failed!" 1>&2
  echo "   Check the error messages above for details" 1>&2
  exit "$exit_code"
fi
