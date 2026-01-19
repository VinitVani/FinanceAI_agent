"""
Price data adapters for fetching OHLC data from external sources.

Adapters:
- CryptoPriceAdapter: Fetches from CoinGecko API
- EquityPriceAdapter: Stub implementation (real API later)

All adapters return DataResponse or DataError (Day 4 contracts).
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

import requests

from .cache import build_cache_key, get_cache
from .contracts import (
    AssetType,
    DataError,
    DataMetadata,
    DataRequest,
    DataResponse,
    ErrorCode,
    OHLCCandle,
)

# TTL Configuration (in seconds)
CRYPTO_TTL = 5 * 60  # 5 minutes
EQUITY_TTL = 15 * 60  # 15 minutes

# API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT = 10  # seconds


class CryptoPriceAdapter:
    """
    Adapter for fetching cryptocurrency prices from CoinGecko.

    CoinGecko API:
    - No API key required for basic usage
    - Rate limit: ~50 calls/minute
    - Free tier sufficient for MVP
    """

    def __init__(self):
        """Initialize adapter."""
        self.base_url = COINGECKO_BASE_URL

    def fetch_prices(self, request: DataRequest) -> Union[DataResponse, DataError]:
        """
        Fetch crypto prices for given request.

        Args:
            request: DataRequest with ticker, dates, etc.

        Returns:
            DataResponse with OHLC data or DataError
        """
        try:
            # Convert ticker format (BTC-USD -> bitcoin)
            coin_id = self._ticker_to_coin_id(request.ticker)
            if not coin_id:
                return DataError(
                    error_code=ErrorCode.INVALID_TICKER,
                    message=f"Unknown crypto ticker: {request.ticker}",
                    retryable=False,
                    original_request=request,
                )

            # Build API request
            # Convert date to Unix timestamp
            start_timestamp = int(
                datetime.combine(request.start_date, datetime.min.time()).timestamp()
            )
            end_timestamp = int(
                datetime.combine(request.end_date, datetime.max.time()).timestamp()
            )

            params = {
                "vs_currency": "usd",
                "from": start_timestamp,
                "to": end_timestamp,
            }

            url = f"{self.base_url}/coins/{coin_id}/market_chart/range"

            # Make API call
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

            # Handle rate limiting
            if response.status_code == 429:
                return DataError(
                    error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    message="CoinGecko rate limit exceeded",
                    retryable=True,
                    original_request=request,
                    details={"retry_after": 60},
                )

            # Handle other errors
            if response.status_code != 200:
                return DataError(
                    error_code=ErrorCode.API_FAILURE,
                    message=f"CoinGecko API error: {response.status_code}",
                    retryable=True,
                    original_request=request,
                )

            # Parse response
            data = response.json()

            # Convert to OHLC format
            ohlc_data = self._convert_to_ohlc(data, request)

            # Build metadata
            metadata = DataMetadata(
                source="coingecko",
                fetched_at=datetime.now(timezone.utc),
                is_complete=len(ohlc_data) > 0,
                missing_dates=[],
                warnings=[],
                cache_hit=False,
            )

            # Return structured response
            return DataResponse(
                request=request,
                metadata=metadata,
                ohlc_data=ohlc_data,
                fundamentals=None,  # Crypto doesn't have fundamentals
                success=True,
            )

        except requests.Timeout:
            return DataError(
                error_code=ErrorCode.API_FAILURE,
                message="CoinGecko API timeout",
                retryable=True,
                original_request=request,
            )
        except Exception as e:
            return DataError(
                error_code=ErrorCode.API_FAILURE,
                message=f"Unexpected error fetching crypto prices: {str(e)}",
                retryable=False,
                original_request=request,
            )

    def _ticker_to_coin_id(self, ticker: str) -> Optional[str]:
        """
        Convert ticker symbol to CoinGecko coin ID.

        Args:
            ticker: Ticker like "BTC-USD", "ETH-USD"

        Returns:
            CoinGecko coin ID or None if unknown
        """
        # Remove -USD suffix if present
        base_ticker = ticker.upper().replace("-USD", "")

        # Map common tickers to CoinGecko IDs
        ticker_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
        }

        return ticker_map.get(base_ticker)

    def _convert_to_ohlc(
        self, api_data: dict, request: DataRequest
    ) -> List[OHLCCandle]:
        """
        Convert CoinGecko response to OHLC candles.

        CoinGecko returns:
        {
            "prices": [[timestamp_ms, price], ...],
            "market_caps": [[timestamp_ms, cap], ...],
            "total_volumes": [[timestamp_ms, volume], ...]
        }

        We need to:
        1. Group by date
        2. Calculate open, high, low, close
        3. Return sorted list of OHLCCandle objects
        """
        prices = api_data.get("prices", [])
        volumes = api_data.get("total_volumes", [])

        if not prices:
            return []

        # Group prices by date
        daily_data = {}
        for timestamp_ms, price in prices:
            date_obj = datetime.fromtimestamp(timestamp_ms / 1000).date()
            if date_obj not in daily_data:
                daily_data[date_obj] = []
            daily_data[date_obj].append(price)

        # Group volumes by date
        daily_volumes = {}
        for timestamp_ms, volume in volumes:
            date_obj = datetime.fromtimestamp(timestamp_ms / 1000).date()
            daily_volumes[date_obj] = volume

        # Create OHLC candles
        candles = []
        for date_obj in sorted(daily_data.keys()):
            prices_for_day = daily_data[date_obj]

            candle = OHLCCandle(
                date=date_obj,
                open=prices_for_day[0],  # First price of day
                high=max(prices_for_day),
                low=min(prices_for_day),
                close=prices_for_day[-1],  # Last price of day
                volume=int(daily_volumes.get(date_obj, 0)),
            )
            candles.append(candle)

        return candles


class EquityPriceAdapter:
    """
    Stub adapter for equity prices.

    Returns fake but valid data for testing.
    Real implementation (Yahoo/Alpha Vantage) comes later.
    """

    def __init__(self):
        """Initialize adapter."""
        pass

    def fetch_prices(self, request: DataRequest) -> Union[DataResponse, DataError]:
        """
        Generate stub equity price data.

        Args:
            request: DataRequest with ticker, dates, etc.

        Returns:
            DataResponse with fake OHLC data
        """
        try:
            # Generate fake data
            ohlc_data = self._generate_stub_data(request)

            metadata = DataMetadata(
                source="equity_stub",
                fetched_at=datetime.now(timezone.utc),
                is_complete=True,
                missing_dates=[],
                warnings=["Using stub data - not real equity prices"],
                cache_hit=False,
            )

            return DataResponse(
                request=request,
                metadata=metadata,
                ohlc_data=ohlc_data,
                fundamentals=None,
                success=True,
            )

        except Exception as e:
            return DataError(
                error_code=ErrorCode.API_FAILURE,
                message=f"Error generating stub data: {str(e)}",
                retryable=False,
                original_request=request,
            )

    def _generate_stub_data(self, request: DataRequest) -> List[OHLCCandle]:
        """Generate fake but realistic-looking OHLC data."""
        candles = []
        current_date = request.start_date
        base_price = 150.0  # Starting price

        while current_date <= request.end_date:
            # Simple random walk
            daily_change = (random.random() - 0.5) * 5

            open_price = base_price
            close_price = base_price + daily_change
            high_price = max(open_price, close_price) * 1.01
            low_price = min(open_price, close_price) * 0.99

            candle = OHLCCandle(
                date=current_date,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=int(1_000_000 + random.random() * 5_000_000),
            )
            candles.append(candle)

            base_price = close_price
            current_date += timedelta(days=1)

        return candles


def get_prices(request: DataRequest) -> Union[DataResponse, DataError]:
    """
    Main entry point for fetching prices.

    This function:
    1. Checks cache first
    2. Routes to correct adapter based on asset type
    3. Caches successful responses
    4. Returns DataResponse or DataError

    Args:
        request: DataRequest with ticker, dates, asset type

    Returns:
        DataResponse or DataError
    """
    # Build cache key
    cache_key = build_cache_key(
        request.ticker,
        request.start_date.isoformat(),
        request.end_date.isoformat(),
    )

    # Check cache first
    cache = get_cache()
    cached_response = cache.get(cache_key)

    if cached_response is not None:
        # Update metadata to indicate cache hit
        # Since metadata is frozen, we need to create a new one
        new_metadata = DataMetadata(
            source=cached_response.metadata.source,
            fetched_at=cached_response.metadata.fetched_at,
            is_complete=cached_response.metadata.is_complete,
            missing_dates=cached_response.metadata.missing_dates,
            warnings=cached_response.metadata.warnings,
            cache_hit=True,
        )
        # Create new response with updated metadata
        return DataResponse(
            request=cached_response.request,
            metadata=new_metadata,
            ohlc_data=cached_response.ohlc_data,
            fundamentals=cached_response.fundamentals,
            success=cached_response.success,
        )

    # Cache miss - fetch from adapter
    if request.asset_type == AssetType.CRYPTO:
        adapter = CryptoPriceAdapter()
        ttl = CRYPTO_TTL
    elif request.asset_type in [AssetType.STOCK, AssetType.ETF]:
        adapter = EquityPriceAdapter()
        ttl = EQUITY_TTL
    else:
        return DataError(
            error_code=ErrorCode.UNSUPPORTED_ASSET_TYPE,
            message=f"Unsupported asset type: {request.asset_type}",
            retryable=False,
            original_request=request,
        )

    # Fetch data
    response = adapter.fetch_prices(request)

    # Cache successful responses only
    if isinstance(response, DataResponse) and response.success:
        cache.set(cache_key, response, ttl)

    return response
