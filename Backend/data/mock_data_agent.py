"""
Mock DataAgent implementation for testing.
Never calls external APIs - safe for CI.
"""

import random
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Union

from .contracts import (
    AssetType,
    DataError,
    DataMetadata,
    DataRequest,
    DataResponse,
    ErrorCode,
    Fundamentals,
    OHLCCandle,
    RequestedField,
)


class MockDataAgent:
    """
    Mock DataAgent for testing without external APIs.

    Usage:
        agent = MockDataAgent()
        response = agent.fetch(request)

        # Simulate errors
        agent = MockDataAgent(mode="error")

        # Simulate partial data
        agent = MockDataAgent(mode="partial")
    """

    def __init__(self, mode: str = "success", seed: Optional[int] = 42):
        """
        Args:
            mode: "success", "partial", "error", "rate_limit", "invalid_ticker"
            seed: Random seed for reproducible data
        """
        self.mode = mode
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def fetch(self, request: DataRequest) -> Union[DataResponse, DataError]:
        """
        Fetch data based on mode.

        Args:
            request: DataRequest with ticker, dates, etc.

        Returns:
            DataResponse or DataError based on mode
        """
        # Route to appropriate handler based on mode
        if self.mode == "error":
            return self._generate_error(request, ErrorCode.API_FAILURE)
        elif self.mode == "rate_limit":
            return self._generate_error(request, ErrorCode.RATE_LIMIT_EXCEEDED)
        elif self.mode == "invalid_ticker":
            return self._generate_error(request, ErrorCode.INVALID_TICKER)
        elif self.mode == "partial":
            return self._generate_partial_data(request)
        else:  # success
            return self._generate_success_data(request)

    def _generate_success_data(self, request: DataRequest) -> DataResponse:
        """Generate complete valid data."""
        ohlc_data = None
        fundamentals_data = None

        # Generate OHLC if requested
        if RequestedField.OHLC in request.requested_fields:
            ohlc_data = self._generate_ohlc(request.start_date, request.end_date)

        # Generate fundamentals if requested
        if RequestedField.FUNDAMENTALS in request.requested_fields:
            fundamentals_data = self._generate_fundamentals(request.asset_type)

        metadata = DataMetadata(
            source="mock",
            fetched_at=datetime.now(timezone.utc),
            is_complete=True,
            missing_dates=[],
            warnings=[],
            cache_hit=False,
        )

        return DataResponse(
            request=request,
            metadata=metadata,
            ohlc_data=ohlc_data,
            fundamentals=fundamentals_data,
            success=True,
        )

    def _generate_partial_data(self, request: DataRequest) -> DataResponse:
        """Generate data with some missing dates."""
        ohlc_data = None

        if RequestedField.OHLC in request.requested_fields:
            # Generate OHLC but skip some dates
            all_candles = self._generate_ohlc(request.start_date, request.end_date)
            # Remove every 3rd candle
            ohlc_data = [c for i, c in enumerate(all_candles) if i % 3 != 0]
            missing = [c.date for i, c in enumerate(all_candles) if i % 3 == 0]
        else:
            missing = []

        metadata = DataMetadata(
            source="mock",
            fetched_at=datetime.now(timezone.utc),
            is_complete=False,
            missing_dates=missing,
            warnings=["Some dates have missing data"],
            cache_hit=False,
        )

        return DataResponse(
            request=request,
            metadata=metadata,
            ohlc_data=ohlc_data,
            fundamentals=None,
            success=True,
        )

    def _generate_error(self, request: DataRequest, error_code: ErrorCode) -> DataError:
        """Generate structured error."""
        messages = {
            ErrorCode.API_FAILURE: ("Mock API failure - external service unavailable"),
            ErrorCode.RATE_LIMIT_EXCEEDED: (
                "Mock rate limit exceeded - retry after 60 seconds"
            ),
            ErrorCode.INVALID_TICKER: (
                f"Mock invalid ticker: {request.ticker} not found"
            ),
        }

        retryable = error_code in {ErrorCode.API_FAILURE, ErrorCode.RATE_LIMIT_EXCEEDED}

        details = {}
        if error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
            details["retry_after"] = 60

        return DataError(
            error_code=error_code,
            message=messages.get(error_code, "Mock error occurred"),
            retryable=retryable,
            missing_fields=None,
            original_request=request,
            details=details if details else None,
        )

    def _generate_ohlc(self, start: date, end: date) -> List[OHLCCandle]:
        """Generate synthetic OHLC data."""
        candles = []
        current = start
        base_price = 100.0 + random.random() * 100  # Random starting price 100-200

        while current <= end:
            # Simple random walk
            daily_change = (random.random() - 0.5) * 5  # +/- 2.5%
            open_price = base_price
            close_price = base_price + daily_change

            # High/low around open/close
            high_price = max(open_price, close_price) * (1 + random.random() * 0.01)
            low_price = min(open_price, close_price) * (1 - random.random() * 0.01)

            volume = int(1_000_000 + random.random() * 5_000_000)

            candles.append(
                OHLCCandle(
                    date=current,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=volume,
                )
            )

            base_price = close_price  # Next day starts where we closed
            current += timedelta(days=1)

        return candles

    def _generate_fundamentals(self, asset_type: AssetType) -> Optional[Fundamentals]:
        """Generate synthetic fundamentals."""
        if asset_type == AssetType.CRYPTO:
            # Crypto doesn't have traditional fundamentals
            return None

        return Fundamentals(
            pe_ratio=15.0 + random.random() * 20,  # 15-35
            market_cap=1_000_000_000 + random.random() * 100_000_000_000,
            revenue=500_000_000 + random.random() * 50_000_000_000,
            eps=1.0 + random.random() * 10,
            dividend_yield=random.random() * 5,  # 0-5%
            beta=0.5 + random.random() * 1.5,  # 0.5-2.0
            currency="USD",
        )
