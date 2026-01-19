from datetime import date
from unittest.mock import Mock, patch

from Backend.data.contracts import AssetType, ErrorCode, RequestedField
from Backend.data.price_adapter import CryptoPriceAdapter, DataRequest


class TestCryptoAdapterInternals:
    def test_ticker_map(self):
        """Test ticker conversion logic."""
        adapter = CryptoPriceAdapter()
        assert adapter._ticker_to_coin_id("BTC-USD") == "bitcoin"
        assert adapter._ticker_to_coin_id("ETH") == "ethereum"
        assert adapter._ticker_to_coin_id("UNKNOWN") is None

    def test_convert_to_ohlc_empty(self):
        """Test conversion with empty data."""
        adapter = CryptoPriceAdapter()
        req = Mock()
        candles = adapter._convert_to_ohlc({"prices": []}, req)
        assert candles == []

    def test_convert_to_ohlc_logic(self):
        """Test OHLC aggregation logic."""
        adapter = CryptoPriceAdapter()
        req = Mock()

        # 2 data points for same day, 1 for next day
        # Timestamp 1704067200000 = 2024-01-01 00:00:00 UTC
        api_data = {
            "prices": [
                [1704067200000, 100.0],  # Day 1 start
                [1704070800000, 110.0],  # Day 1 later
                [1704153600000, 120.0],  # Day 2
            ],
            "total_volumes": [
                [1704067200000, 500.0],
                [1704070800000, 500.0],
                [1704153600000, 2000.0],
            ],
        }

        candles = adapter._convert_to_ohlc(api_data, req)

        assert len(candles) == 2
        # Day 1
        assert candles[0].date == date(2024, 1, 1)
        assert candles[0].open == 100.0
        assert candles[0].high == 110.0
        assert candles[0].low == 100.0
        assert candles[0].close == 110.0
        assert (
            candles[0].volume == 500
        )  # likely last or sum? Logic says: daily_volumes[date_obj] = volume

        # Day 2
        assert candles[1].date == date(2024, 1, 2)
        assert candles[1].close == 120.0

    def test_fetch_timeout(self):
        """Test timeout handling."""
        adapter = CryptoPriceAdapter()
        req = DataRequest(
            ticker="BTC-USD",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1),
            asset_type=AssetType.CRYPTO,
            requested_fields={RequestedField.OHLC},
        )

        import requests

        with patch("requests.get", side_effect=requests.Timeout):
            result = adapter.fetch_prices(req)
            assert result.error_code == ErrorCode.API_FAILURE
            assert "timeout" in result.message

    def test_fetch_generic_exception(self):
        """Test generic exception handling."""
        adapter = CryptoPriceAdapter()
        req = DataRequest(
            ticker="BTC-USD",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1),
            asset_type=AssetType.CRYPTO,
            requested_fields={RequestedField.OHLC},
        )
        with patch("requests.get", side_effect=Exception("Boom")):
            result = adapter.fetch_prices(req)
            assert result.error_code == ErrorCode.API_FAILURE
            assert "Unexpected error" in result.message

    def test_get_prices_crypto_miss(self):
        """Test get_prices with Crypto asset and cache miss."""
        from Backend.data.cache import get_cache
        from Backend.data.price_adapter import get_prices

        get_cache().clear()

        req = DataRequest(
            ticker="BTC-USD",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            asset_type=AssetType.CRYPTO,
            requested_fields={RequestedField.OHLC},
        )

        # Mock fetch to return success
        with patch(
            "Backend.data.price_adapter.CryptoPriceAdapter.fetch_prices"
        ) as mock_fetch:
            # Create a fake success response
            from Backend.data.contracts import DataMetadata, DataResponse

            mock_resp = DataResponse(
                request=req,
                metadata=DataMetadata(
                    source="mock",
                    fetched_at=date(2024, 1, 1),
                    is_complete=True,
                    missing_dates=[],
                    warnings=[],
                    cache_hit=False,
                ),
                ohlc_data=[],
                fundamentals=None,
                success=True,
            )
            mock_fetch.return_value = mock_resp

            result = get_prices(req)
            assert result.success is True
            assert result.metadata.cache_hit is False

    def test_fetch_500_error(self):
        """Test API 500 error handling."""
        adapter = CryptoPriceAdapter()
        req = DataRequest(
            ticker="BTC-USD",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1),
            asset_type=AssetType.CRYPTO,
            requested_fields={RequestedField.OHLC},
        )

        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500

        with patch("requests.get", return_value=mock_response):
            result = adapter.fetch_prices(req)
            assert result.error_code == ErrorCode.API_FAILURE
            assert "CoinGecko API error: 500" in result.message
