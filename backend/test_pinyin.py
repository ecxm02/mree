#!/usr/bin/env python3
"""
Test script to verify pinyin functionality in Elasticsearch
"""
import urllib.request
import urllib.parse
import json

# Elasticsearch endpoint
ES_URL = "http://localhost:9201"

def make_request(url, method="GET", data=None):
    """Make HTTP request without requests library"""
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), response.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

def test_pinyin_setup():
    """Test if pinyin plugin and mapping are working correctly"""
    
    print("=== Testing Pinyin Setup ===\n")
    
    # 1. Check if plugin is loaded
    print("1. Checking if pinyin plugin is loaded...")
    try:
        status, response = make_request(f"{ES_URL}/_cat/plugins?v")
        if status == 200:
            plugins = response
            print(f"Plugins:\n{plugins}")
            if "analysis-pinyin" in plugins:
                print("✅ Pinyin plugin is loaded\n")
            else:
                print("❌ Pinyin plugin NOT found\n")
                return False
        else:
            print(f"❌ Failed to check plugins: {status}\n")
            return False
    except Exception as e:
        print(f"❌ Error checking plugins: {e}\n")
        return False
    
    # 2. Check current mapping
    print("2. Checking current mapping for 'songs' index...")
    try:
        status, response = make_request(f"{ES_URL}/songs/_mapping")
        if status == 200:
            mapping = json.loads(response)
            print(f"Current mapping: {json.dumps(mapping, indent=2)}")
            
            # Check if title field has pinyin analyzer
            title_mapping = mapping.get("songs", {}).get("mappings", {}).get("properties", {}).get("title", {})
            if title_mapping.get("analyzer") == "pinyin_analyzer":
                print("✅ Title field uses pinyin_analyzer\n")
            else:
                print(f"❌ Title field does not use pinyin_analyzer. Current: {title_mapping}\n")
                return False
        else:
            print(f"❌ Failed to get mapping: {status}\n")
            return False
    except Exception as e:
        print(f"❌ Error checking mapping: {e}\n")
        return False
    
    # 3. Test analyzer directly
    print("3. Testing pinyin analyzer directly...")
    try:
        test_data = {
            "analyzer": "pinyin_analyzer",
            "text": "祷告"
        }
        status, response = make_request(f"{ES_URL}/songs/_analyze", "POST", test_data)
        if status == 200:
            result = json.loads(response)
            tokens = [token["token"] for token in result.get("tokens", [])]
            print(f"Analyzer tokens for '祷告': {tokens}")
            if "dao" in tokens or "gao" in tokens or "daogao" in tokens:
                print("✅ Pinyin analyzer is working\n")
            else:
                print("❌ Pinyin analyzer not generating expected tokens\n")
                return False
        else:
            print(f"❌ Failed to test analyzer: {status}\n")
            return False
    except Exception as e:
        print(f"❌ Error testing analyzer: {e}\n")
        return False
    
    # 4. Index a test document and search
    print("4. Testing indexing and search...")
    try:
        # Index test document
        test_doc = {"title": "祷告", "artist": "Test Artist"}
        status, response = make_request(f"{ES_URL}/songs/_doc/test_pinyin", "POST", test_doc)
        if status in [200, 201]:
            print("✅ Test document indexed")
        else:
            print(f"❌ Failed to index test document: {status}")
            return False
        
        # Wait for indexing
        make_request(f"{ES_URL}/songs/_refresh", "POST")
        
        # Search with pinyin
        search_query = {
            "query": {
                "match": {
                    "title": "dao gao"
                }
            }
        }
        status, response = make_request(f"{ES_URL}/songs/_search", "POST", search_query)
        if status == 200:
            result = json.loads(response)
            hits = result.get("hits", {}).get("hits", [])
            if hits:
                print("✅ Pinyin search is working!")
                print(f"Found: {hits[0]['_source']['title']}")
            else:
                print("❌ Pinyin search returned no results")
                return False
        else:
            print(f"❌ Failed to search: {status}")
            return False
            
        # Clean up test document
        make_request(f"{ES_URL}/songs/_doc/test_pinyin", "DELETE")
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False
    
    print("\n🎉 All pinyin tests passed!")
    return True

if __name__ == "__main__":
    test_pinyin_setup()
