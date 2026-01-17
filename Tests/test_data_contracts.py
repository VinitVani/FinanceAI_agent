"""
Unit tests for data contracts.
Tests validate strict schema enforcement.
"""

from datetime import date, timedelta

import pytest

from Backend.data.contracts import (
    AssetType,
    DataError,
    DataRequest,
    DataResponse,
    ErrorCode,
    OHLCCandle,
    RequestedField,
    validate_data_error,
    validate_data_response,
)
from Backend.data.mock_data_agent import MockDataAgent


class TestDataRequest:
    """Test DataRequest validation."""

    def test_valid_request(self):
        """Valid request should pass."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            requested_fields=[RequestedField.OHLC],
        )
        assert req.ticker == "AAPL"  # Uppercase
        assert req.asset_type == AssetType.STOCK

    def test_ticker_normalization(self):
        """Ticker should be uppercased and stripped."""
        req = DataRequest(
            ticker="  aapl  ",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert req.ticker == "AAPL"

    def test_invalid_ticker_empty(self):
        """Empty ticker should fail."""
        with pytest.raises(ValueError, match="empty"):
            DataRequest(
                ticker="",
                asset_type=AssetType.STOCK,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

    def test_invalid_ticker_special_chars(self):
        """Ticker with invalid characters should fail."""
        with pytest.raises(ValueError, match="invalid characters"):
            DataRequest(
                ticker="AA$PL",
                asset_type=AssetType.STOCK,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

    def test_invalid_date_range(self):
        """End date before start date should fail."""
        with pytest.raises(ValueError, match="after start_date"):
            DataRequest(
                ticker="AAPL",
                asset_type=AssetType.STOCK,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1),  # Before start
            )

    def test_future_date_rejected(self):
        """Future end date should fail."""
        future = date.today() + timedelta(days=30)
        with pytest.raises(ValueError, match="future"):
            DataRequest(
                ticker="AAPL",
                asset_type=AssetType.STOCK,
                start_date=date.today(),
                end_date=future,
            )

    def test_request_is_immutable(self):
        """DataRequest should be frozen."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError or similar
            req.ticker = "MSFT"


class TestOHLCCandle:
    """Test OHLC candle validation."""

    def test_valid_candle(self):
        """Valid candle should pass."""
        candle = OHLCCandle(
            date=date(2024, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1_000_000,
        )
        assert candle.high == 105.0

    def test_high_lower_than_low_fails(self):
        """High < low should fail."""
        with pytest.raises(ValueError, match="high must be"):
            OHLCCandle(
                date=date(2024, 1, 1),
                open=100.0,
                high=98.0,  # Lower than low
                low=99.0,
                close=100.0,
            )

    def test_negative_price_fails(self):
        """Negative prices should fail."""
        with pytest.raises(ValueError):
            OHLCCandle(
                date=date(2024, 1, 1),
                open=-100.0,  # Negative
                high=105.0,
                low=99.0,
                close=103.0,
            )

    def test_optional_fields(self):
        """Optional fields can be None."""
        candle = OHLCCandle(
            date=date(2024, 1, 1),
            open=None,
            high=None,
            low=None,
            close=None,
            volume=None,
        )
        assert candle.open is None


class TestDataResponse:
    """Test DataResponse validation."""

    def test_ohlc_must_be_sorted(self):
        """OHLC data must be sorted by date."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
        )

        # Unsorted candles
        candles = [
            OHLCCandle(date=date(2024, 1, 3), close=103.0),
            OHLCCandle(date=date(2024, 1, 1), close=100.0),  # Out of order
            OHLCCandle(date=date(2024, 1, 2), close=101.0),
        ]

        with pytest.raises(ValueError, match="sorted"):
            from Backend.data import DataMetadata

            DataResponse(
                request=req,
                metadata=DataMetadata(source="test"),
                ohlc_data=candles,
            )


class TestDataError:
    """Test DataError structure."""

    def test_valid_error(self):
        """Valid error should pass."""
        error = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="External API is unavailable",
            retryable=True,
        )
        assert error.error_code == ErrorCode.API_FAILURE
        assert error.retryable is True

    def test_error_validation(self):
        """validate_data_error should catch issues."""
        # Too short message
        error = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="Error",  # Too short
            retryable=True,
        )
        assert validate_data_error(error) is False

        # Good message
        error2 = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="External API service is currently unavailable",
            retryable=True,
        )
        assert validate_data_error(error2) is True


class TestMockDataAgent:
    """Test MockDataAgent behavior."""

    def test_success_mode_returns_valid_data(self):
        """Success mode should return valid DataResponse."""
        agent = MockDataAgent(mode="success", seed=42)
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            requested_fields=[RequestedField.OHLC, RequestedField.FUNDAMENTALS],
        )

        response = agent.fetch(req)

        assert isinstance(response, DataResponse)
        assert response.success is True
        assert response.ohlc_data is not None
        assert len(response.ohlc_data) == 10  # 10 days
        assert response.fundamentals is not None
        assert response.metadata.source == "mock"

    def test_partial_mode_has_missing_dates(self):
        """Partial mode should return incomplete data."""
        agent = MockDataAgent(mode="partial", seed=42)
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            requested_fields=[RequestedField.OHLC],
        )

        response = agent.fetch(req)

        assert isinstance(response, DataResponse)
        assert response.metadata.is_complete is False
        assert len(response.metadata.missing_dates) > 0
        assert len(response.metadata.warnings) > 0

    def test_error_mode_returns_data_error(self):
        """Error mode should return DataError."""
        agent = MockDataAgent(mode="error", seed=42)
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
        )

        result = agent.fetch(req)

        assert isinstance(result, DataError)
        assert result.error_code == ErrorCode.API_FAILURE
        assert result.retryable is True

    def test_rate_limit_mode(self):
        """Rate limit mode should return appropriate error."""
        agent = MockDataAgent(mode="rate_limit", seed=42)
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
        )

        result = agent.fetch(req)

        assert isinstance(result, DataError)
        assert result.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert result.retryable is True
        assert result.details is not None
        assert "retry_after" in result.details

    def test_deterministic_with_seed(self):
        """Same seed should produce same data."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            requested_fields=[RequestedField.OHLC],
        )

        agent1 = MockDataAgent(mode="success", seed=42)
        response1 = agent1.fetch(req)

        agent2 = MockDataAgent(mode="success", seed=42)
        response2 = agent2.fetch(req)

        # Same seed = same data
        assert response1.ohlc_data[0].close == response2.ohlc_data[0].close


class TestValidationHelpers:
    """Test validation helper functions."""

    def test_validate_response_missing_requested_field(self):
        """Should warn if requested field is missing."""
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            requested_fields=[RequestedField.OHLC],  # OHLC requested
        )

        from Backend.data import DataMetadata

        response = DataResponse(
            request=req,
            metadata=DataMetadata(source="test"),
            ohlc_data=None,  # But not provided!
        )

        warnings = validate_data_response(response)
        assert len(warnings) > 0
        assert any("OHLC" in w for w in warnings)
