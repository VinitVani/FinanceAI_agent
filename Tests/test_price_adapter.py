"""
Unit tests for price adapters and caching.

Tests verify:
- Cache behavior (hit/miss, TTL)
- Adapter output matches contracts
- Error handling
"""

import time
from datetime import date
from unittest.mock import Mock, patch

from Backend.data import (
    AssetType,
    DataError,
    DataRequest,
    DataResponse,
    ErrorCode,
    RequestedField,
)
from Backend.data.cache import TTLCache, build_cache_key
from Backend.data.price_adapter import (
    CryptoPriceAdapter,
    EquityPriceAdapter,
    get_prices,
)


class TestTTLCache:
    """Test TTL cache behavior."""
    
    def test_get_set_basic(self):
        """Basic get/set should work."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"
    
    def test_get_missing_key(self):
        """Getting missing key should return None."""
        cache = TTLCache()
        assert cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """Expired entries should return None."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl_seconds=1)  # 1 second TTL
        
        # Should exist immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("key1") is None
    
    def test_is_expired(self):
        """is_expired should detect expired entries."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl_seconds=1)
        
        assert not cache.is_expired("key1")
        
        time.sleep(1.1)
        
        assert cache.is_expired("key1")
    
    def test_clear(self):
        """Clear should remove all entries."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        
        assert cache.size() == 2
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get("key1") is None
    
    def test_cleanup_expired(self):
        """cleanup_expired should remove only expired entries."""
        cache = TTLCache()
        cache.set("key1", "value1", ttl_seconds=1)  # Will expire
        cache.set("key2", "value2", ttl_seconds=60)  # Won't expire
        
        time.sleep(1.1)
        
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"


class TestBuildCacheKey:
    """Test cache key building."""
    
    def test_deterministic(self):
        """Same inputs should produce same key."""
        key1 = build_cache_key("AAPL", "2024-01-01", "2024-01-31")
        key2 = build_cache_key("AAPL", "2024-01-01", "2024-01-31")
        assert key1 == key2
    
    def test_different_ticker(self):
        """Different tickers should produce different keys."""
        key1 = build_cache_key("AAPL", "2024-01-01", "2024-01-31")
        key2 = build_cache_key("MSFT", "2024-01-01", "2024-01-31")
        assert key1 != key2
    
    def test_different_dates(self):
        """Different dates should produce different keys."""
        key1 = build_cache_key("AAPL", "2024-01-01", "2024-01-31")
        key2 = build_cache_key("AAPL", "2024-02-01", "2024-02-28")
        assert key1 != key2
    
    def test_case_insensitive_ticker(self):
        """Ticker case should not matter."""
        key1 = build_cache_key("aapl", "2024-01-01", "2024-01-31")
        key2 = build_cache_key("AAPL", "2024-01-01", "2024-01-31")
        assert key1 == key2


class TestEquityPriceAdapter:
    """Test equity adapter (stub)."""
    
    def test_returns_valid_response(self):
        """Stub should return valid DataResponse."""
        adapter = EquityPriceAdapter()
        
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            requested_fields=[RequestedField.OHLC],
        )
        
        response = adapter.fetch_prices(req)
        
        assert isinstance(response, DataResponse)
        assert response.success is True
        assert response.ohlc_data is not None
        assert len(response.ohlc_data) == 5  # 5 days
    
    def test_stub_warning_present(self):
        """Stub should warn about fake data."""
        adapter = EquityPriceAdapter()
        
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        response = adapter.fetch_prices(req)
        
        assert len(response.metadata.warnings) > 0
        assert "stub" in response.metadata.warnings[0].lower()


class TestCryptoPriceAdapter:
    """Test crypto adapter (real API - use mocks)."""
    
    @patch("Backend.data.price_adapter.requests.get")
    def test_successful_fetch(self, mock_get):
        """Successful API call should return valid response."""
        # Mock successful CoinGecko response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "prices": [
                [1704067200000, 42000.0],  # 2024-01-01
                [1704153600000, 43000.0],  # 2024-01-02
            ],
            "market_caps": [],
            "total_volumes": [
                [1704067200000, 1000000000],
                [1704153600000, 1100000000],
            ],
        }
        mock_get.return_value = mock_response
        
        adapter = CryptoPriceAdapter()
        req = DataRequest(
            ticker="BTC-USD",
            asset_type=AssetType.CRYPTO,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            requested_fields=[RequestedField.OHLC],
        )
        
        response = adapter.fetch_prices(req)
        
        assert isinstance(response, DataResponse)
        assert response.success is True
        assert len(response.ohlc_data) > 0
    
    @patch("Backend.data.price_adapter.requests.get")
    def test_rate_limit_handling(self, mock_get):
        """Rate limit should return structured error."""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit
        mock_get.return_value = mock_response
        
        adapter = CryptoPriceAdapter()
        req = DataRequest(
            ticker="BTC-USD",
            asset_type=AssetType.CRYPTO,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
        )
        
        result = adapter.fetch_prices(req)
        
        assert isinstance(result, DataError)
        assert result.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert result.retryable is True
    
    def test_invalid_ticker(self):
        """Unknown ticker should return error."""
        adapter = CryptoPriceAdapter()
        req = DataRequest(
            ticker="INVALID-COIN",
            asset_type=AssetType.CRYPTO,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
        )
        
        result = adapter.fetch_prices(req)
        
        assert isinstance(result, DataError)
        assert result.error_code == ErrorCode.INVALID_TICKER


class TestGetPricesWithCaching:
    """Test main get_prices function with caching."""
    
    def setup_method(self):
        """Clear cache before each test."""
        from Backend.data.cache import get_cache
        get_cache().clear()
    
    def test_cache_miss_then_hit(self):
        """First call misses cache, second call hits."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        # First call - cache miss
        response1 = get_prices(req)
        assert isinstance(response1, DataResponse)
        assert response1.metadata.cache_hit is False
        
        # Second call - cache hit
        response2 = get_prices(req)
        assert isinstance(response2, DataResponse)
        assert response2.metadata.cache_hit is True
        
        # Should be same data
        assert len(response1.ohlc_data) == len(response2.ohlc_data)
    
    def test_different_date_range_cache_miss(self):
        """Different date range should not hit cache."""
        req1 = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        req2 = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 2, 1),  # Different dates
            end_date=date(2024, 2, 5),
        )
        
        response1 = get_prices(req1)
        response2 = get_prices(req2)
        
        # Both should be cache misses
        assert response1.metadata.cache_hit is False
        assert response2.metadata.cache_hit is False
    
    def test_different_ticker_cache_miss(self):
        """Different ticker should not hit cache."""
        req1 = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        req2 = DataRequest(
            ticker="MSFT",  # Different ticker
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        response1 = get_prices(req1)
        response2 = get_prices(req2)
        
        # Both should be cache misses
        assert response1.metadata.cache_hit is False
        assert response2.metadata.cache_hit is False
    
    def test_unsupported_asset_type(self):
        """Unsupported asset type should return error."""
        req = DataRequest(
            ticker="TEST",
            asset_type=AssetType.INDEX,  # Not supported yet
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        result = get_prices(req)
        
        assert isinstance(result, DataError)
        assert result.error_code == ErrorCode.UNSUPPORTED_ASSET_TYPE
