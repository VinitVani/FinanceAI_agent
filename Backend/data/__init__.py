"""Data package for Finance AI Agent."""

from .cache import build_cache_key, get_cache
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
    validate_data_error,
    validate_data_response,
)
from .fundamentals import (
    FundamentalsAdapter,
    MacroDataAdapter,
    get_fundamentals_with_cache,
    get_macro_data_with_cache,
    normalize_fundamentals,
)
from .price_adapter import get_prices

__all__ = [
    "AssetType",
    "DataError",
    "DataMetadata",
    "DataRequest",
    "DataResponse",
    "ErrorCode",
    "Fundamentals",
    "OHLCCandle",
    "RequestedField",
    "validate_data_error",
    "validate_data_response",
    "get_prices",
    "get_cache",
    "build_cache_key",
    "FundamentalsAdapter",
    "MacroDataAdapter",
    "get_fundamentals_with_cache",
    "get_macro_data_with_cache",
    "normalize_fundamentals",
]
