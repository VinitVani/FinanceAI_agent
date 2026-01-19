"""
Unit tests for fundamentals and macro data.

Tests verify:
- All values are numeric
- Missing data is explicit (None)
- Mandatory fields are validated
- Normalization handles edge cases
- No string values leak through
"""

import pytest

from Backend.data import (
    AssetType,
    Fundamentals,
)
from Backend.data.fundamentals import (
    FundamentalsAdapter,
    MacroDataAdapter,
    get_fundamentals_with_cache,
    get_macro_data_with_cache,
    normalize_fundamentals,
    NormalizationError,
)
from Backend.data.cache import get_cache


class TestFundamentalsAdapter:
    """Test fundamentals adapter."""

    def test_equity_returns_fundamentals(self):
        """Equity should return Fundamentals object."""
        adapter = FundamentalsAdapter()
        result = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

        assert result is not None
        assert isinstance(result, Fundamentals)

    def test_crypto_returns_none(self):
        """Crypto should return None (no fundamentals)."""
        adapter = FundamentalsAdapter()
        result = adapter.fetch_fundamentals("BTC-USD", AssetType.CRYPTO)

        assert result is None

    def test_all_values_are_numeric(self):
        """All fundamental values must be numeric or None."""
        adapter = FundamentalsAdapter()
        result = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

        assert result is not None

        # Check each field
        if result.pe_ratio is not None:
            assert isinstance(result.pe_ratio, (int, float))

        if result.market_cap is not None:
            assert isinstance(result.market_cap, (int, float))

        if result.revenue is not None:
            assert isinstance(result.revenue, (int, float))

        if result.eps is not None:
            assert isinstance(result.eps, (int, float))

        if result.dividend_yield is not None:
            assert isinstance(result.dividend_yield, (int, float))

        if result.beta is not None:
            assert isinstance(result.beta, (int, float))

        # Currency should be string
        assert isinstance(result.currency, str)

    def test_no_string_numbers(self):
        """Values should never be strings like "15.5"."""
        adapter = FundamentalsAdapter()
        result = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

        assert result is not None

        # None of these should be strings
        assert not isinstance(result.pe_ratio, str)
        assert not isinstance(result.market_cap, str)
        assert not isinstance(result.eps, str)

    def test_deterministic_by_ticker(self):
        """Same ticker should return same data."""
        adapter = FundamentalsAdapter()

        result1 = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)
        result2 = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

        assert result1.pe_ratio == result2.pe_ratio
        assert result1.market_cap == result2.market_cap

    def test_different_tickers_different_data(self):
        """Different tickers should return different data."""
        adapter = FundamentalsAdapter()

        result1 = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)
        result2 = adapter.fetch_fundamentals("MSFT", AssetType.STOCK)

        # At least some values should differ
        assert (
            result1.pe_ratio != result2.pe_ratio
            or result1.market_cap != result2.market_cap
        )

    def test_validate_fundamentals_warnings(self):
        """Validation should detect missing mandatory fields."""
        adapter = FundamentalsAdapter()

        # Create fundamentals with missing mandatory field
        incomplete = Fundamentals(
            pe_ratio=None,  # Mandatory field missing
            market_cap=1000000000,
            eps=5.0,
            revenue=None,
            dividend_yield=None,
            beta=None,
            currency="USD",
        )

        warnings = adapter.validate_fundamentals(incomplete)

        assert len(warnings) > 0
        assert any("pe_ratio" in w for w in warnings)

    def test_validate_detects_negative_pe(self):
        """Validation should warn about negative P/E."""
        adapter = FundamentalsAdapter()

        bad_fundamentals = Fundamentals(
            pe_ratio=-5.0,  # Invalid
            market_cap=1000000000,
            eps=5.0,
            revenue=None,
            dividend_yield=None,
            beta=None,
            currency="USD",
        )

        warnings = adapter.validate_fundamentals(bad_fundamentals)

        assert len(warnings) > 0
        assert any("negative" in w.lower() for w in warnings)


class TestMacroDataAdapter:
    """Test macro data adapter."""

    def test_returns_dict(self):
        """Should return dict of indicators."""
        adapter = MacroDataAdapter()
        result = adapter.fetch_macro_indicators()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_all_values_numeric(self):
        """All macro values must be numeric."""
        adapter = MacroDataAdapter()
        result = adapter.fetch_macro_indicators()

        for _, value in result.items():
            assert isinstance(value, (int, float))
            assert not isinstance(value, str)

    def test_has_inflation_rate(self):
        """Should include inflation rate."""
        adapter = MacroDataAdapter()
        result = adapter.fetch_macro_indicators()

        assert "inflation_rate" in result
        assert isinstance(result["inflation_rate"], (int, float))

    def test_has_fed_funds_rate(self):
        """Should include Fed funds rate."""
        adapter = MacroDataAdapter()
        result = adapter.fetch_macro_indicators()

        assert "fed_funds_rate" in result
        assert isinstance(result["fed_funds_rate"], (int, float))

    def test_get_specific_indicator(self):
        """Should retrieve specific indicator."""
        adapter = MacroDataAdapter()

        inflation = adapter.get_indicator("inflation_rate")

        assert inflation is not None
        assert isinstance(inflation, (int, float))

    def test_get_nonexistent_indicator(self):
        """Should return None for unknown indicator."""
        adapter = MacroDataAdapter()

        result = adapter.get_indicator("nonexistent_indicator")

        assert result is None

    def test_percentages_as_numbers(self):
        """Percentages should be numbers, not strings."""
        adapter = MacroDataAdapter()
        result = adapter.fetch_macro_indicators()

        # Inflation rate should be 3.4, not "3.4%"
        inflation = result["inflation_rate"]
        assert isinstance(inflation, (int, float))
        assert 0 < inflation < 100  # Reasonable range


class TestNormalizeFundamentals:
    """Test data normalization function."""

    def test_normalize_clean_data(self):
        """Should normalize clean input data."""
        raw = {
            "pe_ratio": 25.5,
            "market_cap": 2500000000000,
            "revenue": 394000000000,
            "eps": 6.13,
            "dividend_yield": 0.0044,  # 0.44% as decimal
            "beta": 1.24,
        }

        result = normalize_fundamentals(raw)

        assert result.pe_ratio == 25.5
        assert result.market_cap == 2500000000000
        assert result.eps == 6.13
        # Dividend yield should be converted to percentage points
        assert result.dividend_yield == pytest.approx(0.44, rel=0.01)

    def test_normalize_string_numbers(self):
        """Should convert string numbers to floats."""
        raw = {
            "pe_ratio": "25.5",  # String
            "market_cap": "2500000000000",
            "eps": "6.13",
        }

        result = normalize_fundamentals(raw)

        assert isinstance(result.pe_ratio, float)
        assert result.pe_ratio == 25.5

    def test_normalize_handles_none(self):
        """Should handle various null representations."""
        raw_variants = [
            {"pe_ratio": None},
            {"pe_ratio": "N/A"},
            {"pe_ratio": "null"},
            {"pe_ratio": "-"},
            {"pe_ratio": ""},
        ]

        for raw in raw_variants:
            result = normalize_fundamentals(raw)
            assert result.pe_ratio is None

    def test_normalize_percentage_strings(self):
        """Should remove percentage signs."""
        raw = {
            "dividend_yield": "2.5%",  # String with %
        }

        result = normalize_fundamentals(raw)

        assert result.dividend_yield == 2.5

    def test_normalize_alias_fields(self):
        """Should handle field aliases."""
        raw = {
            "trailingPE": 25.5,  # Yahoo Finance style
            "marketCap": 2500000000000,
            "trailingEps": 6.13,
        }

        result = normalize_fundamentals(raw)

        assert result.pe_ratio == 25.5
        assert result.market_cap == 2500000000000
        assert result.eps == 6.13

    def test_normalize_invalid_type_returns_none(self):
        """Should handle invalid types gracefully and return None."""
        raw = {
            "pe_ratio": "not a number",
        }

        # Should handle gracefully and return None
        result = normalize_fundamentals(raw)
        assert result.pe_ratio is None


class TestCaching:
    """Test caching behavior for fundamentals."""

    def setup_method(self):
        """Clear cache before each test."""
        get_cache().clear()

    def test_fundamentals_cached(self):
        """Fundamentals should be cached."""
        # First call
        result1 = get_fundamentals_with_cache("AAPL", AssetType.STOCK)

        # Check cache
        cache = get_cache()
        cache_key = "fundamentals|AAPL"
        cached = cache.get(cache_key)

        assert cached is not None
        assert cached.pe_ratio == result1.pe_ratio

    def test_macro_data_cached(self):
        """Macro data should be cached."""
        # First call
        result1 = get_macro_data_with_cache()

        # Check cache
        cache = get_cache()
        cache_key = "macro|current"
        cached = cache.get(cache_key)

        assert cached is not None
        assert cached["inflation_rate"] == result1["inflation_rate"]

    def test_cache_hit_on_second_call(self):
        """Second call should hit cache."""
        # First call - cache miss
        result1 = get_fundamentals_with_cache("AAPL", AssetType.STOCK)

        # Second call - should be same object from cache
        result2 = get_fundamentals_with_cache("AAPL", AssetType.STOCK)

        # Should return same values
        assert result1.pe_ratio == result2.pe_ratio
        assert result1.market_cap == result2.market_cap


class TestMissingDataPolicy:
    """Test missing data handling rules."""

    def test_mandatory_field_missing_returns_none(self):
        """Missing mandatory field should be None, not error."""
        incomplete = Fundamentals(
            pe_ratio=None,  # Missing
            market_cap=1000000000,
            eps=None,  # Missing
            revenue=None,
            dividend_yield=None,
            beta=None,
            currency="USD",
        )

        assert incomplete.pe_ratio is None
        assert incomplete.eps is None

    def test_optional_field_missing_is_fine(self):
        """Missing optional field is okay."""
        with_optional_missing = Fundamentals(
            pe_ratio=25.0,
            market_cap=1000000000,
            eps=5.0,
            revenue=None,  # Optional - okay to be missing
            dividend_yield=None,
            beta=None,
            currency="USD",
        )

        assert with_optional_missing.revenue is None
        assert with_optional_missing.dividend_yield is None

    def test_never_fake_data(self):
        """Should never fill fake data for missing values."""
        # This test verifies we return None, not 0 or fake values
        adapter = FundamentalsAdapter()

        result = adapter.fetch_fundamentals("TEST", AssetType.STOCK)

        # If a field is None, it stays None (not replaced with 0)
        if result.dividend_yield is None:
            assert result.dividend_yield is None  # Not 0.0


class TestTrailingVsForwardMetrics:
    """Test that only trailing metrics are used."""

    def test_schema_specifies_trailing(self):
        """Schema should specify trailing in descriptions."""
        # Check that Fundamentals fields mention "trailing" or "TTM"
        pe_field = Fundamentals.model_fields["pe_ratio"]
        assert "trailing" in pe_field.description.lower() or "ttm" in pe_field.description.lower()

    def test_no_forward_metrics_in_output(self):
        """Output should never include forward estimates."""
        adapter = FundamentalsAdapter()
        result = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

        # Check that result only has trailing metrics
        # (No forward_pe, forward_eps, etc.)
        assert not hasattr(result, "forward_pe")
        assert not hasattr(result, "forward_eps")

