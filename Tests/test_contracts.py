from datetime import date, timedelta

import pytest

from Backend.data.contracts import (
    AssetType,
    DataError,
    DataMetadata,
    DataRequest,
    DataResponse,
    ErrorCode,
    OHLCCandle,
    RequestedField,
    validate_data_error,
    validate_data_response,
)


class TestContracts:
    def test_validate_ticker(self):
        with pytest.raises(ValueError, match="Ticker cannot be empty"):
            DataRequest(
                ticker="",
                asset_type=AssetType.STOCK,
                start_date=date.today(),
                end_date=date.today(),
            )

        with pytest.raises(ValueError, match="Ticker must be 20 characters or less"):
            DataRequest(
                ticker="A" * 21,
                asset_type=AssetType.STOCK,
                start_date=date.today(),
                end_date=date.today(),
            )

        with pytest.raises(ValueError, match="Ticker contains invalid characters"):
            DataRequest(
                ticker="BTC$USD",
                asset_type=AssetType.STOCK,
                start_date=date.today(),
                end_date=date.today(),
            )

    def test_validate_date_range(self):
        d1 = date(2023, 1, 1)
        d2 = date(2023, 1, 2)

        # End before start
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            DataRequest(
                ticker="AAPL", asset_type=AssetType.STOCK, start_date=d2, end_date=d1
            )

        # Future end date
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValueError, match="end_date cannot be in the future"):
            DataRequest(
                ticker="AAPL",
                asset_type=AssetType.STOCK,
                start_date=date.today(),
                end_date=future,
            )

    def test_ohlc_relationships(self):
        d = date(2023, 1, 1)
        # High < Low
        with pytest.raises(ValueError, match="high must be >= low"):
            OHLCCandle(date=d, open=10, high=8, low=9, close=10)

        # High < Open
        with pytest.raises(ValueError, match="high must be >= open"):
            OHLCCandle(date=d, open=10, high=9, low=8, close=9)

        # High < Close
        with pytest.raises(ValueError, match="high must be >= close"):
            OHLCCandle(date=d, open=9, high=9, low=8, close=10)

    def test_validate_data_response_warnings(self):
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 5),
            requested_fields=[RequestedField.OHLC, RequestedField.FUNDAMENTALS],
        )
        meta = DataMetadata(source="test", is_complete=False)

        # Missing OHLC and Fundamentals
        resp = DataResponse(
            request=req, metadata=meta, ohlc_data=None, fundamentals=None
        )
        warnings = validate_data_response(resp)
        assert "OHLC data was requested but not provided" in warnings
        assert "Fundamentals were requested but not provided" in warnings

        # Partial data coverage
        # 5 days expected, only 1 provided
        resp2 = DataResponse(
            request=req,
            metadata=meta,
            ohlc_data=[
                OHLCCandle(
                    date=date(2023, 1, 1), open=1, high=1, low=1, close=1, volume=1
                )
            ],
            fundamentals=None,
        )
        warnings2 = validate_data_response(resp2)
        assert any("Only 1 days of data" in w for w in warnings2)

    def test_validate_data_error(self):
        # Good error
        err = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="Long enough failure message",
            retryable=True,
        )
        assert validate_data_error(err) is True

        # Short message
        err_short = DataError(
            error_code=ErrorCode.API_FAILURE, message="Short", retryable=True
        )
        assert validate_data_error(err_short) is False

        # Retryable code but retryable=False
        err_retry = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="Valid failure message here",
            retryable=False,
        )
        assert validate_data_error(err_retry) is False
