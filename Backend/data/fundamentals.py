"""
Fundamentals and macro data fetchers.

This module provides clean, normalized numeric data for analysis.

Key principles:
- All values are numeric (float/int), never strings
- Only trailing (TTM) metrics, never forward estimates
- Missing data is explicit (None), never faked
- Mandatory fields are flagged if missing
"""

from typing import Optional, Dict, Any, List
import random

from .contracts import (
    AssetType,
    Fundamentals,
)
from .cache import get_cache


# Cache TTL for fundamentals (longer than price data)
FUNDAMENTALS_TTL = 60 * 60  # 1 hour (fundamentals change slowly)
MACRO_TTL = 60 * 60 * 24  # 24 hours (macro data changes daily at most)


class FundamentalsAdapter:
    """
    Adapter for fetching company fundamentals.

    For MVP: Returns stub data.
    Later: Replace with real API (Yahoo Finance, Alpha Vantage, etc.)

    Rules:
    - Only trailing (TTM) metrics
    - All values numeric
    - Missing data = None (explicit)
    - Crypto returns None (no fundamentals)
    """

    def __init__(self):
        """Initialize adapter."""
        self.mandatory_fields = ["pe_ratio", "eps", "market_cap"]

    def fetch_fundamentals(
        self, ticker: str, asset_type: AssetType
    ) -> Optional[Fundamentals]:
        """
        Fetch fundamentals for given ticker.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            asset_type: Type of asset

        Returns:
            Fundamentals object or None if not applicable/available
        """
        # Crypto has no fundamentals
        if asset_type == AssetType.CRYPTO:
            return None

        # For MVP: Return realistic stub data
        # Later: Replace with real API call
        return self._generate_stub_fundamentals(ticker)

    def _generate_stub_fundamentals(self, ticker: str) -> Fundamentals:
        """
        Generate realistic stub fundamentals.

        This creates fake but plausible data for testing.
        Values vary by ticker for consistency.
        """
        # Use ticker hash for deterministic randomness
        seed = hash(ticker) % 10000
        random.seed(seed)

        # Generate realistic values (all trailing/TTM-style)
        pe_ratio = 10.0 + random.random() * 40.0  # 10-50
        market_cap = (
            100_000_000_000 + random.random() * 2_000_000_000_000
        )  # 100B-2T
        revenue = market_cap * (0.3 + random.random() * 0.5)  # 30-80% of market cap
        eps = random.random() * 20.0  # 0-20
        dividend_yield = (
            random.random() * 4.0 if random.random() > 0.3 else None
        )  # 0-4% or None
        beta = 0.5 + random.random() * 1.5  # 0.5-2.0

        return Fundamentals(
            pe_ratio=round(pe_ratio, 2),
            market_cap=round(market_cap, 2),
            revenue=round(revenue, 2),
            eps=round(eps, 2),
            dividend_yield=round(dividend_yield, 2) if dividend_yield else None,
            beta=round(beta, 2),
            currency="USD",
        )

    def validate_fundamentals(self, fundamentals: Optional[Fundamentals]) -> List[str]:
        """
        Validate fundamentals and return warnings.

        Args:
            fundamentals: Fundamentals object to validate

        Returns:
            List of warnings (empty if all good)
        """
        if fundamentals is None:
            return ["Fundamentals not available for this asset type"]

        warnings: List[str] = []

        # Check mandatory fields
        for field in self.mandatory_fields:
            value = getattr(fundamentals, field, None)
            if value is None:
                warnings.append(f"Mandatory field '{field}' is missing")

        # Check for unrealistic values (data quality check)
        if fundamentals.pe_ratio is not None:
            if fundamentals.pe_ratio < 0:
                warnings.append("P/E ratio is negative (possible data error)")
            if fundamentals.pe_ratio > 1000:
                warnings.append("P/E ratio is unusually high (>1000)")

        if fundamentals.market_cap is not None and fundamentals.market_cap < 0:
            warnings.append("Market cap is negative (data error)")

        return warnings


class MacroDataAdapter:
    """
    Adapter for fetching macro economic indicators.

    For MVP: Returns stub data.
    Later: Replace with FRED API or similar.

    Indicators:
    - Inflation (CPI YoY)
    - Interest rates (Fed Funds Rate)
    """

    def __init__(self):
        """Initialize adapter."""
        pass

    def fetch_macro_indicators(self) -> Dict[str, float]:
        """
        Fetch current macro economic indicators.

        Returns:
            Dict with indicator names and numeric values
            Example: {"inflation_rate": 3.2, "fed_funds_rate": 5.25}
        """
        # For MVP: Return plausible current values
        # Later: Replace with real FRED API call
        return self._get_stub_macro_data()

    def _get_stub_macro_data(self) -> Dict[str, float]:
        """
        Generate stub macro data.

        Values are realistic as of 2024-2025.
        """
        return {
            "inflation_rate": 3.4,  # CPI YoY as percentage (not "3.4%")
            "fed_funds_rate": 5.25,  # Federal funds rate as percentage
            "gdp_growth": 2.5,  # GDP growth rate YoY
            "unemployment_rate": 3.7,  # Unemployment rate
        }

    def get_indicator(self, indicator_name: str) -> Optional[float]:
        """
        Get specific macro indicator.

        Args:
            indicator_name: Name of indicator (e.g., "inflation_rate")

        Returns:
            Numeric value or None if not found
        """
        indicators = self.fetch_macro_indicators()
        return indicators.get(indicator_name)


class NormalizationError(Exception):
    """Raised when data normalization fails."""

    pass


def normalize_fundamentals(raw_data: Dict[str, Any]) -> Fundamentals:
    """
    Normalize raw fundamentals data to standard schema.

    This function handles common normalization issues:
    - Converting strings to numbers
    - Removing percentage signs
    - Standardizing units
    - Handling various null representations

    Args:
        raw_data: Raw data dict from API

    Returns:
        Normalized Fundamentals object

    Raises:
        NormalizationError: If data cannot be normalized
    """
    normalized: Dict[str, Any] = {}

    # Define field mappings and normalization rules
    field_rules: Dict[str, Dict[str, Any]] = {
        "pe_ratio": {
            "aliases": ["pe_ratio", "pe", "trailingPE", "trailing_pe"],
            "type": float,
            "allow_none": True,
        },
        "market_cap": {
            "aliases": ["market_cap", "marketCap", "market_capitalization"],
            "type": float,
            "allow_none": True,
        },
        "revenue": {
            "aliases": ["revenue", "totalRevenue", "total_revenue", "ttm_revenue"],
            "type": float,
            "allow_none": True,
        },
        "eps": {
            "aliases": ["eps", "trailingEps", "trailing_eps"],
            "type": float,
            "allow_none": True,
        },
        "dividend_yield": {
            "aliases": ["dividend_yield", "dividendYield", "yield"],
            "type": float,
            "allow_none": True,
            "percentage": True,  # Convert 0.035 -> 3.5
        },
        "beta": {
            "aliases": ["beta", "beta3Year"],
            "type": float,
            "allow_none": True,
        },
    }

    # Normalize each field
    for field, rules in field_rules.items():
        value: Any = None

        # Try each alias
        for alias in rules["aliases"]:
            if alias in raw_data:
                value = raw_data[alias]
                break

        # Handle null representations
        if value in [None, "", "N/A", "null", "None", "-"]:
            normalized[field] = None
            continue

        # Convert to correct type
        try:
            if rules["type"] == float:
                # Remove percentage signs if present
                if isinstance(value, str):
                    value = value.replace("%", "").strip()

                value = float(value)

                # Convert decimal percentage to percentage points if needed
                if rules.get("percentage") and value < 1.0:
                    value = value * 100

                normalized[field] = value
            else:
                normalized[field] = rules["type"](value)

        except (ValueError, TypeError):
            if rules["allow_none"]:
                normalized[field] = None
            else:
                raise NormalizationError(
                    f"Cannot normalize field '{field}' with value '{value}'"
                )

    # Always set currency
    normalized["currency"] = raw_data.get("currency", "USD")

    return Fundamentals(**normalized)


def get_fundamentals_with_cache(
    ticker: str, asset_type: AssetType
) -> Optional[Fundamentals]:
    """
    Get fundamentals with caching.

    Args:
        ticker: Stock ticker
        asset_type: Type of asset

    Returns:
        Fundamentals object or None
    """
    # Build cache key
    cache_key = f"fundamentals|{ticker.upper()}"

    # Check cache
    cache = get_cache()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch fresh data
    adapter = FundamentalsAdapter()
    fundamentals = adapter.fetch_fundamentals(ticker, asset_type)

    # Cache result (even if None)
    cache.set(cache_key, fundamentals, FUNDAMENTALS_TTL)

    return fundamentals


def get_macro_data_with_cache() -> Dict[str, float]:
    """
    Get macro indicators with caching.

    Returns:
        Dict of macro indicators
    """
    cache_key = "macro|current"

    # Check cache
    cache = get_cache()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch fresh data
    adapter = MacroDataAdapter()
    macro_data = adapter.fetch_macro_indicators()

    # Cache result
    cache.set(cache_key, macro_data, MACRO_TTL)

    return macro_data


# ============================================================================
# MISSING DATA HANDLING RULES (documented here)
# ============================================================================

"""
MISSING DATA POLICY:

1. Mandatory fields (pe_ratio, eps, market_cap):
   - If missing: Set to None
   - Flag with warning
   - Still return Fundamentals object

2. Optional fields (revenue, dividend_yield, beta):
   - If missing: Set to None
   - No warning required

3. All fundamentals missing:
   - Return None (not empty Fundamentals object)
   - Caller should check for None

4. Crypto assets:
   - Always return None (crypto has no fundamentals)
   - This is expected behavior

5. NEVER:
   - Fill fake data for missing values
   - Return 0 instead of None
   - Drop fields silently
   - Use forward estimates

TRAILING vs FORWARD METRICS:

ALWAYS use trailing (TTM) metrics:
- pe_ratio → Trailing P/E
- eps → Trailing EPS
- revenue → TTM revenue

NEVER use forward estimates:
- Forward P/E
- Forward EPS
- Forward revenue estimates

Why? Forward metrics are:
- Subjective estimates
- Often mixed unknowingly
- Source of silent bugs
- Not comparable across sources
"""

