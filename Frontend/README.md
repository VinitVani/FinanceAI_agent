# AI Finance Agent - Frontend

## Overview
Minimal Streamlit frontend for the AI Finance Agent MVP.

## Features
- 💬 Chat interface for querying financial data
- 📁 CSV portfolio upload
- 📊 Portfolio preview and validation
- 🔗 Backend API integration (stub for Day 7)

## Running Locally

### Prerequisites
```bash
pip install streamlit pandas
```

### Start the app
```bash
cd Frontend
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Project Structure
```
Frontend/
├── app.py              # Main Streamlit application
├── components/         # Reusable UI components (future)
├── utils/              # Helper functions
│   └── helpers.py
└── README.md
```

## Design Principles

### Frontend is DUMB
- No business logic
- No LLM calls
- No data analysis
- Only: collect input, display output

### Backend Does Everything
- All analysis in Backend/
- All data processing in Backend/
- Frontend just shows results

## CSV Upload Format

Portfolio CSV must have these columns:
- `ticker`: Stock/crypto ticker (e.g., AAPL, BTC-USD)
- `quantity`: Number of shares/coins

Example:
```csv
ticker,quantity
AAPL,10
MSFT,5
BTC-USD,0.5
```

## Current Status

**Day 7 (Current):**
- ✅ Chat UI
- ✅ CSV upload
- ✅ Message history
- ✅ Portfolio preview
- ✅ Stub backend connection

**Coming Next:**
- Day 8: Real backend API integration
- Day 9: Planner Agent
- Day 10: Analysis Agent
- Day 12: End-to-end flow

## Development Notes

### State Management
Uses Streamlit's built-in session_state:
- `messages`: Chat message history
- `uploaded_portfolio`: Filename of uploaded CSV
- `portfolio_df`: Parsed portfolio DataFrame

### Backend Connection
Currently uses stub function `send_to_backend_stub()`.
Replace in Day 8 with real API calls.

## Troubleshooting

### Port already in use
```bash
streamlit run app.py --server.port 8502
```

### Changes not reflecting
Streamlit auto-reloads. If issues, stop and restart:
```bash
# Stop: Ctrl+C
# Start: streamlit run app.py
```

### Import errors
Make sure you're in the project root and Backend is accessible:
```python
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent / "Backend"
sys.path.insert(0, str(backend_path))
```
