
import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from Backend.data.price_adapter import (
    CryptoPriceAdapter,
    EquityPriceAdapter,
    get_prices,
    CRYPTO_TTL,
    EQUITY_TTL
)
from Backend.data.contracts import (
    DataRequest,
    AssetType,
    RequestedField,
    ErrorCode,
    DataResponse,
    DataError
)
from Backend.data.cache import get_cache

# Mock requests.get response
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

def test_crypto_adapter_success():
    adapter = CryptoPriceAdapter()
    request = DataRequest(
        ticker="BTC-USD",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 2),
        asset_type=AssetType.CRYPTO,
        requested_fields={RequestedField.OHLC}
    )
    
    mock_data = {
        "prices": [
            [1672531200000, 16500.0],
            [1672617600000, 16600.0]
        ],
        "total_volumes": [
            [1672531200000, 1000000.0],
            [1672617600000, 1100000.0]
        ]
    }
    
    with patch("requests.get", return_value=MockResponse(mock_data, 200)):
        result = adapter.fetch_prices(request)
        
    assert isinstance(result, DataResponse)
    assert result.success is True
    assert len(result.ohlc_data) == 2
    assert result.ohlc_data[0].close == 16500.0

def test_crypto_adapter_invalid_ticker():
    adapter = CryptoPriceAdapter()
    request = DataRequest(
        ticker="INVALID",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.CRYPTO,
        requested_fields={RequestedField.OHLC}
    )
    
    result = adapter.fetch_prices(request)
    
    assert isinstance(result, DataError)
    assert result.error_code == ErrorCode.INVALID_TICKER

def test_crypto_adapter_rate_limit():
    adapter = CryptoPriceAdapter()
    request = DataRequest(
        ticker="BTC-USD",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.CRYPTO,
        requested_fields={RequestedField.OHLC}
    )
    
    with patch("requests.get", return_value=MockResponse({}, 429)):
        result = adapter.fetch_prices(request)
        
    assert isinstance(result, DataError)
    assert result.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
    assert result.retryable is True

def test_equity_adapter_stub():
    adapter = EquityPriceAdapter()
    request = DataRequest(
        ticker="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 5),
        asset_type=AssetType.STOCK,
        requested_fields={RequestedField.OHLC}
    )
    
    result = adapter.fetch_prices(request)
    
    assert isinstance(result, DataResponse)
    assert result.success is True
    assert len(result.ohlc_data) > 0
    assert result.metadata.source == "equity_stub"

def test_get_prices_cache_hit():
    # Setup cache
    cache = get_cache()
    cache.clear()
    
    request = DataRequest(
        ticker="BTC-USD",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.CRYPTO,
        requested_fields={RequestedField.OHLC}
    )
    
    # Manually seed cache
    from Backend.data.contracts import DataMetadata
    metadata = DataMetadata(
        source="test",
        fetched_at=datetime.now(),
        is_complete=True,
        missing_dates=[],
        warnings=[],
        cache_hit=False,
    )
    
    mock_response = DataResponse(
        request=request,
        metadata=metadata,
        ohlc_data=[],
        fundamentals=None,
        success=True
    )
    
    # We need to construct the cache key manually to seed it
    from Backend.data.cache import build_cache_key
    key = build_cache_key(request.ticker, request.start_date.isoformat(), request.end_date.isoformat())
    cache.set(key, mock_response, 60)
    
    # Test fetch
    result = get_prices(request)
    
    assert isinstance(result, DataResponse)
    assert result.metadata.cache_hit is True

def test_get_prices_unsupported():
    request = DataRequest(
        ticker="UNK",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.INDEX,  # Not supported yet
        requested_fields={RequestedField.OHLC}
    )
    
    result = get_prices(request)
    
    assert isinstance(result, DataError)
    assert result.error_code == ErrorCode.UNSUPPORTED_ASSET_TYPE
