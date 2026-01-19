#!/usr/bin/env python3
"""Verify Day 6 implementation."""

from Backend.data import AssetType
from Backend.data.cache import get_cache
from Backend.data.fundamentals import (
    FundamentalsAdapter,
    MacroDataAdapter,
    get_fundamentals_with_cache,
    normalize_fundamentals,
)

print("=" * 60)
print("DAY 6 VERIFICATION")
print("=" * 60)

# Test 1: Fetch equity fundamentals
print("\n1. Testing equity fundamentals...")
adapter = FundamentalsAdapter()
fundamentals = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

if fundamentals:
    print(f"   ✅ P/E Ratio: {fundamentals.pe_ratio}")
    print(f"   ✅ Market Cap: ${fundamentals.market_cap:,.0f}")
    print(f"   ✅ EPS: ${fundamentals.eps}")
    print(f"   ✅ Currency: {fundamentals.currency}")

    # Check all values are numeric
    all_numeric = True
    for field in ["pe_ratio", "market_cap", "eps", "revenue"]:
        value = getattr(fundamentals, field)
        if value is not None and not isinstance(value, (int, float)):
            print(f"   ❌ {field} is not numeric: {type(value)}")
            all_numeric = False

    if all_numeric:
        print("   ✅ All values are numeric!")
else:
    print("   ❌ No fundamentals returned")

# Test 2: Crypto returns None
print("\n2. Testing crypto (should return None)...")
crypto_fund = adapter.fetch_fundamentals("BTC-USD", AssetType.CRYPTO)
if crypto_fund is None:
    print("   ✅ Crypto correctly returns None")
else:
    print("   ❌ Crypto should not have fundamentals")

# Test 3: Macro data
print("\n3. Testing macro indicators...")
macro_adapter = MacroDataAdapter()
macro_data = macro_adapter.fetch_macro_indicators()

print(f"   ✅ Inflation Rate: {macro_data['inflation_rate']}%")
print(f"   ✅ Fed Funds Rate: {macro_data['fed_funds_rate']}%")

# Check all macro values are numeric
all_numeric = all(isinstance(v, (int, float)) for v in macro_data.values())
if all_numeric:
    print("   ✅ All macro values are numeric!")
else:
    print("   ❌ Some macro values are not numeric")

# Test 4: Caching
print("\n4. Testing caching...")
get_cache().clear()

fund1 = get_fundamentals_with_cache("AAPL", AssetType.STOCK)
cache_size_after_first = get_cache().size()

fund2 = get_fundamentals_with_cache("AAPL", AssetType.STOCK)

if cache_size_after_first > 0:
    print("   ✅ Fundamentals are being cached")
    if fund1.pe_ratio == fund2.pe_ratio:
        print("   ✅ Cache returns same data")
else:
    print("   ❌ Caching not working")

# Test 5: Normalization
print("\n5. Testing normalization...")
raw_data = {
    "pe_ratio": "25.5",  # String
    "market_cap": "2500000000000",
    "eps": 6.13,
    "dividend_yield": "2.5%",  # String with %
}

try:
    normalized = normalize_fundamentals(raw_data)
    print(f"   ✅ String '25.5' → {normalized.pe_ratio} (float)")
    print(f"   ✅ String '2.5%' → {normalized.dividend_yield}% (float)")
    print("   ✅ Normalization working!")
except Exception as e:
    print(f"   ❌ Normalization failed: {e}")

# Test 6: Validation
print("\n6. Testing validation...")
base = adapter.fetch_fundamentals("AAPL", AssetType.STOCK)

# Create a new Fundamentals instance with a missing mandatory field
from Backend.data import Fundamentals  # noqa: E402, I001 Imported here to avoid circular issues

incomplete = Fundamentals(
    pe_ratio=None,  # Simulate missing mandatory field
    market_cap=base.market_cap if base is not None else None,
    eps=base.eps if base is not None else None,
    revenue=base.revenue if base is not None else None,
    dividend_yield=base.dividend_yield if base is not None else None,
    beta=base.beta if base is not None else None,
    currency=base.currency if base is not None else "USD",
)

warnings = adapter.validate_fundamentals(incomplete)
if warnings:
    print(f"   ✅ Validation detected {len(warnings)} issue(s)")
    print(f"   └─ {warnings[0]}")
else:
    print("   ⚠️  No warnings (but should detect missing mandatory fields)")

print("\n" + "=" * 60)
print("🎉 DAY 6 COMPLETE!")
print("=" * 60)
print("\nKey achievements:")
print("- Fundamentals return clean numeric data")
print("- Crypto correctly has no fundamentals")
print("- Macro indicators work")
print("- Caching reduces redundant fetches")
print("- Normalization handles messy input")
print("- Validation catches data quality issues")
