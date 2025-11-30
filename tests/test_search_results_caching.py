# tests/test_search_results_caching.py
import pytest
from src.data_retrieval.cache import SearchResultsCache

def test_result_caching():
    """Test caching and retrieving search results."""
    cache = SearchResultsCache()
    
    test_query = "artificial intelligence"
    test_results = [
        {"title": "AI Overview", "source": "academic"},
        {"title": "Latest AI Trends", "source": "blog"}
    ]
    
    # Cache results
    cache.store_results(test_query, test_results)
    
    # Retrieve cached results
    cached_results = cache.get_results(test_query)
    
    assert cached_results is not None
    assert len(cached_results) == len(test_results)

def test_cache_expiration():
    """Test cache result expiration."""
    cache = SearchResultsCache(expiration_hours=1)
    
    test_query = "machine learning algorithms"
    test_results = [{"title": "ML Algorithms 2024"}]
    
    cache.store_results(test_query, test_results)
    
    # Simulate time passing
    import time
    time.sleep(2)  # Simulate 2 hours passing
    
    expired_results = cache.get_results(test_query)
    assert expired_results is None