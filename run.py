#!/usr/bin/env python3
"""Quick start script for Digital Store Bot."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import main

if __name__ == "__main__":
    print("🚀 Starting Digital Store Bot...")
    print("📖 For full documentation, see README.md")
    print("⚙️  Configure your .env file before running")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)