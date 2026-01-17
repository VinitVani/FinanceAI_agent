"""
Data contracts for Finance AI Agent.
Defines exact schemas for all DataAgent interactions.
"""

from __future__ import annotations

from datetime import date as date_type, datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# 1. Define Enums
class AssetType(str, Enum):
    """Supported asset types."""
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"
    INDEX = "index"


class RequestedField(str, Enum):
    """Fields that can be requested from DataAgent."""
    OHLC = "ohlc"
    FUNDAMENTALS = "fundamentals"
    VOLUME = "volume"
    METADATA = "metadata"


class ErrorCode(str, Enum):
    """Standardized error codes."""
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    INVALID_TICKER = "INVALID_TICKER"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    API_FAILURE = "API_FAILURE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNSUPPORTED_ASSET_TYPE = "UNSUPPORTED_ASSET_TYPE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    PARTIAL_DATA = "PARTIAL_DATA"


# 2. Define INPUT schema (DataRequest)
class DataRequest(BaseModel):
    """Request schema for DataAgent. What PlannerAgent sends to DataAgent."""
    
    ticker: str = Field(..., description="Stock/crypto symbol (e.g., 'AAPL', 'BTC-USD')")
    asset_type: AssetType = Field(..., description="Type of asset")
    start_date: date_type = Field(..., description="Start date for data")
    end_date: date_type = Field(..., description="End date for data")
    requested_fields: List[RequestedField] = Field(
        default=[RequestedField.OHLC],
        description="What data to include"
    )
    
    model_config = {"frozen": True}
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate and normalize ticker."""
        v = v.strip().upper()
        if not v:
            raise ValueError("Ticker cannot be empty")
        if len(v) > 20:
            raise ValueError("Ticker must be 20 characters or less")
        if not all(c.isalnum() or c in ["-", "."] for c in v):
            raise ValueError("Ticker contains invalid characters")
        return v
    
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date_type, info) -> date_type:
        """Validate date range."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        if v > date_type.today():
            raise ValueError("end_date cannot be in the future")
        return v


# 3. Define OUTPUT components
class OHLCCandle(BaseModel):
    """Single price candle for OHLC data."""
    
    date: date_type = Field(..., description="The date")
    open: Optional[float] = Field(default=None, description="Opening price", ge=0)
    high: Optional[float] = Field(default=None, description="Highest price", ge=0)
    low: Optional[float] = Field(default=None, description="Lowest price", ge=0)
    close: Optional[float] = Field(default=None, description="Closing price", ge=0)
    volume: Optional[int] = Field(default=None, description="Trading volume", ge=0)
    
    model_config = {"frozen": True}
    
    @model_validator(mode="after")
    def validate_price_relationships(self):
        """Validate price relationships when values exist."""
        if self.high is not None and self.low is not None:
            if self.high < self.low:
                raise ValueError("high must be >= low")
        
        if self.high is not None and self.open is not None:
            if self.high < self.open:
                raise ValueError("high must be >= open")
        
        if self.high is not None and self.close is not None:
            if self.high < self.close:
                raise ValueError("high must be >= close")
        
        return self


class Fundamentals(BaseModel):
    """Company metrics and fundamentals."""
    
    pe_ratio: Optional[float] = Field(None, description="P/E ratio")
    market_cap: Optional[float] = Field(None, description="Market cap in USD", ge=0)
    revenue: Optional[float] = Field(None, description="Annual revenue in USD", ge=0)
    eps: Optional[float] = Field(None, description="Earnings per share")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield %", ge=0, le=100)
    beta: Optional[float] = Field(None, description="Beta coefficient")
    currency: str = Field(default="USD", description="Currency")
    
    model_config = {"frozen": True}


class DataMetadata(BaseModel):
    """Fetch metadata about the data retrieval."""
    
    source: str = Field(..., description="Data source name (e.g., 'yahoo', 'coingecko')")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When fetched"
    )
    is_complete: bool = Field(default=True, description="All requested data present?")
    missing_dates: List[date_type] = Field(default_factory=list, description="Dates with missing data")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    cache_hit: bool = Field(default=False, description="From cache?")
    
    model_config = {"frozen": True}


# 4. Define OUTPUT schema (DataResponse)
class DataResponse(BaseModel):
    """Response schema from DataAgent. What AnalysisAgent receives."""
    
    request: DataRequest = Field(..., description="Original request for reference")
    metadata: DataMetadata = Field(..., description="Fetch metadata")
    ohlc_data: Optional[List[OHLCCandle]] = Field(
        None,
        description="OHLC candles if requested"
    )
    fundamentals: Optional[Fundamentals] = Field(
        None,
        description="Fundamentals if requested"
    )
    success: bool = Field(default=True, description="Was fetch successful?")
    
    model_config = {"frozen": True}
    
    @field_validator("ohlc_data")
    @classmethod
    def validate_ohlc_sorted(cls, v: Optional[List[OHLCCandle]]) -> Optional[List[OHLCCandle]]:
        """Ensure OHLC data is sorted by date."""
        if v is None or len(v) <= 1:
            return v
        dates = [candle.date for candle in v]
        if dates != sorted(dates):
            raise ValueError("OHLC data must be sorted by date")
        return v


# 5. Define ERROR schema (DataError)
class DataError(BaseModel):
    """Structured error from DataAgent. NEVER throw exceptions - always return DataError."""
    
    error_code: ErrorCode = Field(..., description="Standardized error code")
    message: str = Field(..., description="Human-readable message")
    retryable: bool = Field(default=False, description="Can retry?")
    missing_fields: Optional[List[str]] = Field(
        None,
        description="Fields that were unavailable"
    )
    original_request: Optional[DataRequest] = Field(
        None,
        description="Request that caused error"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context"
    )
    
    model_config = {"frozen": True}


# 6. Add validation helpers
def validate_data_response(response: DataResponse) -> List[str]:
    """
    Additional validation for DataResponse.
    Returns list of warnings (empty if all good).
    """
    warnings = []
    
    # Check if requested fields are present
    request = response.request
    if RequestedField.OHLC in request.requested_fields and response.ohlc_data is None:
        warnings.append("OHLC data was requested but not provided")
    
    if RequestedField.FUNDAMENTALS in request.requested_fields and response.fundamentals is None:
        warnings.append("Fundamentals were requested but not provided")
    
    # Check date coverage
    if response.ohlc_data:
        dates = {candle.date for candle in response.ohlc_data}
        expected_days = (request.end_date - request.start_date).days + 1
        if len(dates) < expected_days * 0.5:  # Less than 50% coverage
            warnings.append(f"Only {len(dates)} days of data out of {expected_days} expected")
    
    return warnings


def validate_data_error(error: DataError) -> bool:
    """Validate error schema is properly constructed."""
    if len(error.message) < 10:
        return False
    
    retryable_codes = {ErrorCode.API_FAILURE, ErrorCode.RATE_LIMIT_EXCEEDED}
    if error.error_code in retryable_codes and not error.retryable:
        return False
    
    return True


"""
MISSING DATA HANDLING RULES:

1. Price missing for some dates:
   - Return partial OHLC data
   - Set metadata.is_complete = False
   - List missing dates in metadata.missing_dates
   - Add warning to metadata.warnings

2. Fundamentals missing:
   - Set individual fields to None (not entire object)
   - Document which fields are None
   - Add warning if critical fields missing

3. API failure:
   - Return DataError with appropriate error_code
   - Set retryable = True if transient
   - Include details for debugging

4. Invalid ticker:
   - Return DataError with INVALID_TICKER
   - Set retryable = False
   - Suggest similar tickers in details if possible

5. Rate limit:
   - Return DataError with RATE_LIMIT_EXCEEDED
   - Set retryable = True
   - Include retry_after in details if available

CRITICAL: NEVER silently drop data. ALWAYS use structured errors.
"""
