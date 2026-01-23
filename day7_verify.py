#!/usr/bin/env python3
"""Verify Day 7 frontend implementation."""

import sys
from pathlib import Path
import subprocess

print("=" * 60)
print("DAY 7 VERIFICATION")
print("=" * 60)

# Check file structure
print("\n1. Checking file structure...")
required_files = [
    "Frontend/app.py",
    "Frontend/__init__.py",
    "Frontend/components/__init__.py",
    "Frontend/utils/__init__.py",
    "Frontend/utils/helpers.py",
    "Frontend/README.md",
]

all_exist = True
for file_path in required_files:
    if Path(file_path).exists():
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ Missing: {file_path}")
        all_exist = False

if not all_exist:
    print("\n❌ File structure incomplete")
    sys.exit(1)

# Check Streamlit installed
print("\n2. Checking Streamlit installation...")
try:
    import streamlit
    print(f"   ✅ Streamlit {streamlit.__version__} installed")
except ImportError:
    print("   ❌ Streamlit not installed")
    print("   Run: pip3 install streamlit pandas")
    sys.exit(1)

# Check pandas installed
print("\n3. Checking pandas installation...")
try:
    import pandas
    print(f"   ✅ Pandas {pandas.__version__} installed")
except ImportError:
    print("   ❌ Pandas not installed")
    print("   Run: pip3 install pandas")
    sys.exit(1)

# Check app.py can be imported
print("\n4. Checking app.py syntax...")
try:
    # Try to compile the file
    with open("Frontend/app.py", "r") as f:
        code = f.read()
    compile(code, "Frontend/app.py", "exec")
    print("   ✅ app.py has no syntax errors")
except SyntaxError as e:
    print(f"   ❌ Syntax error in app.py: {e}")
    sys.exit(1)

# Check helpers.py
print("\n5. Checking utils/helpers.py...")
try:
    sys.path.insert(0, str(Path("Frontend").absolute()))
    from utils.helpers import validate_portfolio_csv, format_currency
    print("   ✅ Helper functions importable")
except Exception as e:
    print(f"   ❌ Error importing helpers: {e}")
    sys.exit(1)

# Test helper functions
print("\n6. Testing helper functions...")
try:
    # Test format_currency
    result = format_currency(1234.56)
    assert result == "$1,234.56", f"Expected $1,234.56, got {result}"
    print("   ✅ format_currency works")
    
    # Test format_percentage
    from utils.helpers import format_percentage
    result = format_percentage(12.345)
    assert result == "12.35%", f"Expected 12.35%, got {result}"
    print("   ✅ format_percentage works")
    
except Exception as e:
    print(f"   ❌ Helper function error: {e}")
    sys.exit(1)

# Instructions for manual testing
print("\n" + "=" * 60)
print("🎉 DAY 7 AUTOMATED CHECKS PASSED!")
print("=" * 60)
print("\n📋 MANUAL TESTING REQUIRED:")
print("\n1. Start the Streamlit app:")
print("   cd Frontend")
print("   streamlit run app.py")
print("\n2. Verify in browser (http://localhost:8501):")
print("   ✅ Page loads without errors")
print("   ✅ Chat input box visible (Full width)")
print("   ✅ Can type and send messages")
print("   ✅ Messages appear in chat history")
print("   ✅ CSV upload widget visible in sidebar")
print("   ✅ Can upload sample_portfolio.csv")
print("   ✅ Portfolio preview shows correctly")

print("\n3. Test chat:")
print("   - Type: 'What is AAPL stock price?'")
print("   - Should see stub response (Text only, no emojis)")

print("\n4. Test CSV upload:")
print("   - Upload Frontend/sample_portfolio.csv")
print("   - Should see portfolio preview")
print("   - Should show position count")
print("\nIf all manual checks pass → Day 7 is COMPLETE! 🚀")
