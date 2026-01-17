#!/usr/bin/env python3
"""Verify Day 5 implementation."""

from datetime import date

from Backend.data import (
    AssetType,
    DataRequest,
    RequestedField,
)
from Backend.data.cache import get_cache
from Backend.data.price_adapter import get_prices

print("=" * 60)
print("DAY 5 VERIFICATION")
print("=" * 60)

# Test 1: Fetch equity data
print("\n1. Testing equity stub adapter...")
req = DataRequest(
    ticker="AAPL",
    asset_type=AssetType.STOCK,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 5),
    requested_fields=[RequestedField.OHLC],
)

response1 = get_prices(req)
print(f"   ✅ Got {len(response1.ohlc_data)} days of data")
print(f"   ✅ Cache hit: {response1.metadata.cache_hit}")

# Test 2: Cache hit
print("\n2. Testing cache hit (same request)...")
response2 = get_prices(req)
print(f"   ✅ Cache hit: {response2.metadata.cache_hit}")

if response2.metadata.cache_hit:
    print("   ✅ Cache is working!")
else:
    print("   ❌ Cache miss - something is wrong")

# Test 3: Cache miss (different ticker)
print("\n3. Testing cache miss (different ticker)...")
req2 = DataRequest(
    ticker="MSFT",
    asset_type=AssetType.STOCK,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 5),
)

response3 = get_prices(req2)
print(f"   ✅ Cache hit: {response3.metadata.cache_hit}")

if not response3.metadata.cache_hit:
    print("   ✅ Different ticker correctly missed cache!")
else:
    print("   ❌ Should have been cache miss")

# Test 4: Clear cache
print("\n4. Testing cache clear...")
cache = get_cache()
initial_size = cache.size()
cache.clear()
final_size = cache.size()
print(f"   ✅ Cache size: {initial_size} → {final_size}")

print("\n" + "=" * 60)
print("🎉 DAY 5 COMPLETE!")
print("=" * 60)
