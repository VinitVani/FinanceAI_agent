"""
Utility functions for frontend.

These are pure helper functions with no business logic.
"""

from typing import Optional

import pandas as pd


def format_currency(amount: float) -> str:
    """Format number as USD currency."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage."""
    return f"{value:.2f}%"


def validate_portfolio_csv(df: pd.DataFrame) -> tuple[bool, Optional[str]]:
    """
    Validate portfolio CSV structure.

    Args:
        df: DataFrame to validate

    Returns:
        (is_valid, error_message)
    """
    required_columns = ["ticker", "quantity"]

    # Check columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"

    # Check data types
    if not pd.api.types.is_numeric_dtype(df["quantity"]):
        return False, "Column 'quantity' must be numeric"

    # Check for empty
    if len(df) == 0:
        return False, "CSV is empty"

    # Check for negative quantities
    if (df["quantity"] < 0).any():
        return False, "Quantities cannot be negative"

    return True, None


def create_sample_portfolio_csv() -> str:
    """
    Create sample portfolio CSV content.

    Returns:
        CSV content as string
    """
    return """ticker,quantity
AAPL,10
MSFT,5
GOOGL,3
BTC-USD,0.5
ETH-USD,2"""
