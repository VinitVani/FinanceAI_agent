"""
TTL-specific cache tests.

These tests verify time-based cache expiration.
"""

import time
from datetime import date

import pytest

from Backend.data import AssetType, DataRequest
from Backend.data.cache import get_cache
from Backend.data.price_adapter import get_prices


class TestCacheTTL:
    """Test cache TTL expiration."""
    
    def setup_method(self):
        """Clear cache before each test."""
        get_cache().clear()
    
    def test_equity_ttl_longer_than_crypto(self):
        """Equity TTL should be longer than crypto TTL."""
        from Backend.data.price_adapter import CRYPTO_TTL, EQUITY_TTL
        
        assert EQUITY_TTL > CRYPTO_TTL
    
    def test_cache_expires_after_ttl(self):
        """Cache should expire after TTL seconds."""
        cache = get_cache()
        
        # Set with 1 second TTL
        cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should exist immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        assert cache.get("test_key") is None
    
    @pytest.mark.slow
    def test_cached_response_expires(self):
        """Full integration: cached response should expire."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
        )
        
        # Temporarily set short TTL for testing
        from Backend.data import price_adapter
        original_ttl = price_adapter.EQUITY_TTL
        price_adapter.EQUITY_TTL = 2  # 2 seconds
        
        try:
            # First call
            response1 = get_prices(req)
            assert response1.metadata.cache_hit is False
            
            # Second call immediately - should hit cache
            response2 = get_prices(req)
            assert response2.metadata.cache_hit is True
            
            # Wait for expiration
            time.sleep(2.5)
            
            # Third call after expiration - should miss cache
            response3 = get_prices(req)
            assert response3.metadata.cache_hit is False
            
        finally:
            # Restore original TTL
            price_adapter.EQUITY_TTL = original_ttl
