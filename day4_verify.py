#!/usr/bin/env python3
"""
Day 4 Verification Script
Verifies all Day 4 requirements are met.
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Backend.data.contracts import (
    AssetType,
    DataError,
    DataMetadata,
    DataRequest,
    DataResponse,
    ErrorCode,
    Fundamentals,
    OHLCCandle,
    RequestedField,
    validate_data_error,
    validate_data_response,
)
from Backend.data.mock_data_agent import MockDataAgent


def check_file_exists(filepath: Path) -> Tuple[bool, str]:
    """Check if required file exists."""
    if filepath.exists():
        return True, f"✅ {filepath} exists"
    return False, f"❌ {filepath} MISSING"


def check_input_schema() -> List[Tuple[bool, str]]:
    """Verify INPUT schema (DataRequest) requirements."""
    results = []
    
    # Test 1: Valid request should work
    try:
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            requested_fields=[RequestedField.OHLC],
        )
        results.append((True, "✅ DataRequest accepts valid input"))
    except Exception as e:
        results.append((False, f"❌ DataRequest failed on valid input: {e}"))
    
    # Test 2: Invalid ticker should be rejected
    try:
        DataRequest(
            ticker="",  # Empty ticker
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        results.append((False, "❌ DataRequest should reject empty ticker"))
    except ValueError:
        results.append((True, "✅ DataRequest rejects invalid ticker"))
    
    # Test 3: Invalid date range should be rejected
    try:
        DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 31),
            end_date=date(2024, 1, 1),  # End before start
        )
        results.append((False, "❌ DataRequest should reject invalid date range"))
    except ValueError:
        results.append((True, "✅ DataRequest rejects invalid date range"))
    
    # Test 4: Ticker normalization
    try:
        req = DataRequest(
            ticker="  aapl  ",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        if req.ticker == "AAPL":
            results.append((True, "✅ DataRequest normalizes ticker (uppercase, strip)"))
        else:
            results.append((False, f"❌ Ticker normalization failed: got {req.ticker}"))
    except Exception as e:
        results.append((False, f"❌ Ticker normalization error: {e}"))
    
    return results


def check_output_schema() -> List[Tuple[bool, str]]:
    """Verify OUTPUT schema (DataResponse) requirements."""
    results = []
    
    # Test 1: Valid response structure
    try:
        req = DataRequest(
            ticker="AAPL",
            asset_type=AssetType.STOCK,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
        )
        
        candles = [
            OHLCCandle(date=date(2024, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0),
            OHLCCandle(date=date(2024, 1, 2), open=103.0, high=108.0, low=102.0, close=106.0),
            OHLCCandle(date=date(2024, 1, 3), open=106.0, high=110.0, low=105.0, close=109.0),
        ]
        
        metadata = DataMetadata(source="test", fetched_at=datetime.now(timezone.utc))
        response = DataResponse(
            request=req,
            metadata=metadata,
            ohlc_data=candles,
            fundamentals=None,
        )
        
        results.append((True, "✅ DataResponse accepts valid structure"))
        
        # Test 2: OHLC must be sorted
        unsorted_candles = [
            OHLCCandle(date=date(2024, 1, 3), close=109.0),
            OHLCCandle(date=date(2024, 1, 1), close=103.0),  # Out of order
        ]
        
        try:
            DataResponse(
                request=req,
                metadata=metadata,
                ohlc_data=unsorted_candles,
            )
            results.append((False, "❌ DataResponse should reject unsorted OHLC"))
        except ValueError:
            results.append((True, "✅ DataResponse enforces sorted OHLC"))
        
    except Exception as e:
        results.append((False, f"❌ DataResponse validation error: {e}"))
    
    # Test 3: Metadata structure
    try:
        metadata = DataMetadata(
            source="test",
            fetched_at=datetime.now(timezone.utc),
            is_complete=True,
            missing_dates=[],
            warnings=[],
        )
        results.append((True, "✅ DataMetadata has all required fields"))
    except Exception as e:
        results.append((False, f"❌ DataMetadata error: {e}"))
    
    # Test 4: Fundamentals structure
    try:
        fundamentals = Fundamentals(
            pe_ratio=25.0,
            market_cap=1_000_000_000,
            revenue=500_000_000,
            currency="USD",
        )
        results.append((True, "✅ Fundamentals schema is valid"))
    except Exception as e:
        results.append((False, f"❌ Fundamentals error: {e}"))
    
    return results


def check_error_schema() -> List[Tuple[bool, str]]:
    """Verify ERROR schema (DataError) requirements."""
    results = []
    
    # Test 1: Valid error structure
    try:
        error = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="External API is unavailable",
            retryable=True,
        )
        results.append((True, "✅ DataError accepts valid structure"))
    except Exception as e:
        results.append((False, f"❌ DataError creation error: {e}"))
    
    # Test 2: Error validation
    try:
        # Too short message should fail validation
        bad_error = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="Error",  # Too short
            retryable=True,
        )
        if not validate_data_error(bad_error):
            results.append((True, "✅ Error validation catches bad messages"))
        else:
            results.append((False, "❌ Error validation should reject short messages"))
        
        # Good error should pass
        good_error = DataError(
            error_code=ErrorCode.API_FAILURE,
            message="External API service is currently unavailable",
            retryable=True,
        )
        if validate_data_error(good_error):
            results.append((True, "✅ Error validation accepts good errors"))
        else:
            results.append((False, "❌ Error validation should accept valid errors"))
    except Exception as e:
        results.append((False, f"❌ Error validation error: {e}"))
    
    # Test 3: All error codes exist
    required_codes = [
        ErrorCode.DATA_NOT_FOUND,
        ErrorCode.INVALID_TICKER,
        ErrorCode.INVALID_DATE_RANGE,
        ErrorCode.API_FAILURE,
        ErrorCode.RATE_LIMIT_EXCEEDED,
    ]
    for code in required_codes:
        try:
            error = DataError(error_code=code, message="Test error message")
            results.append((True, f"✅ ErrorCode.{code.name} exists"))
        except Exception as e:
            results.append((False, f"❌ ErrorCode.{code.name} error: {e}"))
    
    return results


def check_mock_data_agent() -> List[Tuple[bool, str]]:
    """Verify MockDataAgent requirements."""
    results = []
    
    req = DataRequest(
        ticker="AAPL",
        asset_type=AssetType.STOCK,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 10),
        requested_fields=[RequestedField.OHLC, RequestedField.FUNDAMENTALS],
    )
    
    # Test 1: Success mode returns valid DataResponse
    try:
        agent = MockDataAgent(mode="success", seed=42)
        response = agent.fetch(req)
        
        if isinstance(response, DataResponse):
            if response.success and response.ohlc_data and response.fundamentals:
                results.append((True, "✅ MockDataAgent success mode returns valid DataResponse"))
            else:
                results.append((False, "❌ MockDataAgent success mode missing data"))
        else:
            results.append((False, f"❌ MockDataAgent success mode returned {type(response)}"))
    except Exception as e:
        results.append((False, f"❌ MockDataAgent success mode error: {e}"))
    
    # Test 2: Partial mode returns incomplete data
    try:
        agent = MockDataAgent(mode="partial", seed=42)
        response = agent.fetch(req)
        
        if isinstance(response, DataResponse):
            if not response.metadata.is_complete and len(response.metadata.missing_dates) > 0:
                results.append((True, "✅ MockDataAgent partial mode returns incomplete data"))
            else:
                results.append((False, "❌ MockDataAgent partial mode should have missing dates"))
        else:
            results.append((False, f"❌ MockDataAgent partial mode returned {type(response)}"))
    except Exception as e:
        results.append((False, f"❌ MockDataAgent partial mode error: {e}"))
    
    # Test 3: Error mode returns DataError
    try:
        agent = MockDataAgent(mode="error", seed=42)
        result = agent.fetch(req)
        
        if isinstance(result, DataError):
            if result.error_code == ErrorCode.API_FAILURE and result.retryable:
                results.append((True, "✅ MockDataAgent error mode returns DataError"))
            else:
                results.append((False, "❌ MockDataAgent error mode has wrong error structure"))
        else:
            results.append((False, f"❌ MockDataAgent error mode returned {type(result)}"))
    except Exception as e:
        results.append((False, f"❌ MockDataAgent error mode error: {e}"))
    
    # Test 4: Rate limit mode
    try:
        agent = MockDataAgent(mode="rate_limit", seed=42)
        result = agent.fetch(req)
        
        if isinstance(result, DataError):
            if result.error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
                results.append((True, "✅ MockDataAgent rate_limit mode works"))
            else:
                results.append((False, "❌ MockDataAgent rate_limit mode wrong error code"))
        else:
            results.append((False, f"❌ MockDataAgent rate_limit mode returned {type(result)}"))
    except Exception as e:
        results.append((False, f"❌ MockDataAgent rate_limit mode error: {e}"))
    
    return results


def check_missing_data_handling() -> List[Tuple[bool, str]]:
    """Verify missing data handling rules are documented."""
    results = []
    
    # Check if contracts.py has the documentation
    contracts_file = project_root / "Backend" / "data" / "contracts.py"
    if contracts_file.exists():
        content = contracts_file.read_text()
        
        required_rules = [
            "Price missing for some dates",
            "Fundamentals missing",
            "API failure",
            "Invalid ticker",
            "NEVER silently drop data",
        ]
        
        for rule in required_rules:
            if rule.lower() in content.lower():
                results.append((True, f"✅ Missing data rule documented: {rule}"))
            else:
                results.append((False, f"❌ Missing data rule not found: {rule}"))
    else:
        results.append((False, "❌ contracts.py not found"))
    
    return results


def main():
    """Run all Day 4 verification checks."""
    print("=" * 70)
    print("DAY 4 VERIFICATION - DataAgent Interface & Contracts")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Check 1: Required files exist
    print("📁 Checking required files...")
    required_files = [
        project_root / "Backend" / "data" / "contracts.py",
        project_root / "Backend" / "data" / "mock_data_agent.py",
        project_root / "Tests" / "test_data_contracts.py",
    ]
    
    for filepath in required_files:
        exists, msg = check_file_exists(filepath)
        print(f"  {msg}")
        if not exists:
            all_passed = False
    print()
    
    # Check 2: INPUT schema
    print("📥 Checking INPUT schema (DataRequest)...")
    input_results = check_input_schema()
    for passed, msg in input_results:
        print(f"  {msg}")
        if not passed:
            all_passed = False
    print()
    
    # Check 3: OUTPUT schema
    print("📤 Checking OUTPUT schema (DataResponse)...")
    output_results = check_output_schema()
    for passed, msg in output_results:
        print(f"  {msg}")
        if not passed:
            all_passed = False
    print()
    
    # Check 4: ERROR schema
    print("❌ Checking ERROR schema (DataError)...")
    error_results = check_error_schema()
    for passed, msg in error_results:
        print(f"  {msg}")
        if not passed:
            all_passed = False
    print()
    
    # Check 5: MockDataAgent
    print("🎭 Checking MockDataAgent...")
    mock_results = check_mock_data_agent()
    for passed, msg in mock_results:
        print(f"  {msg}")
        if not passed:
            all_passed = False
    print()
    
    # Check 6: Missing data handling
    print("📋 Checking missing data handling rules...")
    missing_results = check_missing_data_handling()
    for passed, msg in missing_results:
        print(f"  {msg}")
        if not passed:
            all_passed = False
    print()
    
    # Final summary
    print("=" * 70)
    if all_passed:
        print("✅ DAY 4 VERIFICATION: ALL CHECKS PASSED")
        print()
        print("Exit Criteria Check:")
        print("  ✅ Input schema rejects invalid requests")
        print("  ✅ Output schema is strictly validated")
        print("  ✅ Error schema is consistent")
        print("  ✅ MockDataAgent returns valid data")
        print("  ✅ Unit tests exist and validate schemas")
        print()
        print("🎉 Day 4 is COMPLETE!")
    else:
        print("❌ DAY 4 VERIFICATION: SOME CHECKS FAILED")
        print()
        print("Please review the failures above and fix them.")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
