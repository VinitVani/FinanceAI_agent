import os
import sys

# Ensure backend modules are in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend.core.config import get_settings


def main():
    print("Starting FinanceAI Agent Backend...")
    settings = get_settings()
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print("Service initialized (Day 1 Placeholder)")


if __name__ == "__main__":
    main()
