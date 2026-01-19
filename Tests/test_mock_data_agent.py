
import pytest
from datetime import date
from Backend.data.mock_data_agent import MockDataAgent
from Backend.data.contracts import (
    DataRequest,
    AssetType,
    RequestedField,
    ErrorCode,
    DataResponse,
    DataError
)

def test_mock_agent_success():
    agent = MockDataAgent(mode="success", seed=42)
    request = DataRequest(
        ticker="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 5),
        asset_type=AssetType.STOCK,
        requested_fields={RequestedField.OHLC, RequestedField.FUNDAMENTALS}
    )
    
    response = agent.fetch(request)
    
    assert isinstance(response, DataResponse)
    assert response.success is True
    assert response.ohlc_data is not None
    assert len(response.ohlc_data) > 0
    assert response.fundamentals is not None
    assert response.metadata.is_complete is True

def test_mock_agent_partial():
    agent = MockDataAgent(mode="partial", seed=42)
    request = DataRequest(
        ticker="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 10),
        asset_type=AssetType.STOCK,
        requested_fields={RequestedField.OHLC}
    )
    
    response = agent.fetch(request)
    
    assert isinstance(response, DataResponse)
    assert response.success is True
    assert response.metadata.is_complete is False
    assert len(response.metadata.missing_dates) > 0

def test_mock_agent_error_mode():
    agent = MockDataAgent(mode="error")
    request = DataRequest(
        ticker="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.STOCK,
        requested_fields={RequestedField.OHLC}
    )
    
    response = agent.fetch(request)
    
    assert isinstance(response, DataError)
    assert response.error_code == ErrorCode.API_FAILURE

def test_mock_agent_rate_limit():
    agent = MockDataAgent(mode="rate_limit")
    request = DataRequest(
        ticker="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.STOCK,
        requested_fields={RequestedField.OHLC}
    )
    
    response = agent.fetch(request)
    
    assert isinstance(response, DataError)
    assert response.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
    assert response.details["retry_after"] == 60

def test_mock_agent_fundamentals_crypto():
    agent = MockDataAgent(mode="success")
    request = DataRequest(
        ticker="BTC-USD",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 1),
        asset_type=AssetType.CRYPTO,
        requested_fields={RequestedField.FUNDAMENTALS}
    )
    
    response = agent.fetch(request)
    
    assert isinstance(response, DataResponse)
    assert response.fundamentals is None  # Crypto has no fundamentals in mock
