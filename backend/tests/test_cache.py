"""Tests for cache functionality."""

import pytest
from cache import CacheClient


@pytest.mark.unit
def test_cache_client_initialization(mock_redis):
    """Test cache client initializes correctly."""
    cache = CacheClient(redis_url="redis://localhost:6379/0")
    assert cache.redis_url == "redis://localhost:6379/0"


@pytest.mark.unit
def test_generate_cache_key():
    """Test cache key generation is consistent and normalized."""
    cache = CacheClient()

    # Same inputs should produce same key
    key1 = cache.generate_cache_key("test query", ["NIV", "ESV"], {"testament": "NT"})
    key2 = cache.generate_cache_key("test query", ["ESV", "NIV"], {"testament": "NT"})
    assert key1 == key2, "Cache keys should be identical for same inputs regardless of order"

    # Case-insensitive queries
    key3 = cache.generate_cache_key("Test Query", ["NIV"], None)
    key4 = cache.generate_cache_key("test query", ["NIV"], None)
    assert key3 == key4, "Cache keys should be case-insensitive"

    # Different inputs produce different keys
    key5 = cache.generate_cache_key("different query", ["NIV"], None)
    assert key1 != key5, "Different queries should produce different keys"


@pytest.mark.unit
def test_cache_results(mock_redis):
    """Test caching search results."""
    cache = CacheClient()
    cache._client = mock_redis

    cache_key = "test_key_123"
    results = {
        "query_time_ms": 150,
        "results": [{"verse": "Genesis 1:1"}],
        "search_metadata": {"total_results": 1},
    }

    success = cache.cache_results(cache_key, results, "test query")
    assert success is True

    # Verify setex was called
    assert mock_redis.setex.called


@pytest.mark.unit
def test_get_cached_results(mock_redis):
    """Test retrieving cached results."""
    import json

    cache = CacheClient()
    cache._client = mock_redis

    cached_data = {
        "query_time_ms": 100,
        "results": [{"verse": "John 3:16"}],
    }
    mock_redis.get.return_value = json.dumps(cached_data)

    result = cache.get_cached_results("test_key")
    assert result is not None
    assert result["query_time_ms"] == 100
    assert len(result["results"]) == 1


@pytest.mark.unit
def test_cache_embedding(mock_redis):
    """Test caching embeddings."""
    cache = CacheClient()
    cache._client = mock_redis

    text = "test text"
    embedding = [0.1, 0.2, 0.3, 0.4] * 256  # 1024 dimensions

    success = cache.cache_embedding(text, embedding)
    assert success is True
    assert mock_redis.setex.called


@pytest.mark.unit
def test_get_cached_embedding(mock_redis):
    """Test retrieving cached embeddings."""
    import json

    cache = CacheClient()
    cache._client = mock_redis

    embedding = [0.1] * 1024
    mock_redis.get.return_value = json.dumps(embedding)

    result = cache.get_cached_embedding("test text")
    assert result is not None
    assert len(result) == 1024


@pytest.mark.unit
def test_is_connected_success(mock_redis):
    """Test cache connection check when connected."""
    cache = CacheClient()
    cache._client = mock_redis
    mock_redis.ping.return_value = True

    assert cache.is_connected() is True


@pytest.mark.unit
def test_is_connected_failure(mock_redis):
    """Test cache connection check when disconnected."""
    import redis

    cache = CacheClient()
    cache._client = mock_redis
    mock_redis.ping.side_effect = redis.ConnectionError("Connection failed")

    assert cache.is_connected() is False


@pytest.mark.unit
def test_clear_search_cache(mock_redis):
    """Test clearing search cache."""
    cache = CacheClient()
    cache._client = mock_redis

    mock_redis.keys.side_effect = [
        ["search:key1", "search:key2"],  # search keys
        ["stats:key1", "stats:key2"],    # stats keys
    ]
    mock_redis.delete.return_value = 4

    deleted = cache.clear_search_cache()
    assert deleted == 4


@pytest.mark.unit
def test_get_cache_stats(mock_redis):
    """Test retrieving cache statistics."""
    cache = CacheClient()
    cache._client = mock_redis

    mock_redis.info.return_value = {
        "used_memory_human": "1.5M",
        "uptime_in_seconds": 3600,
    }
    mock_redis.keys.return_value = ["search:1", "search:2"]

    stats = cache.get_cache_stats()
    assert stats["connected"] is True
    assert stats["used_memory"] == "1.5M"
    assert stats["cached_searches"] == 2
