#!/usr/bin/env python3
"""Check that all imports work correctly."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

errors = []

print("🔍 Checking imports...\n")

# Core modules
print("Checking core modules...")
try:
    from src.catchup.core import config
    print("  ✅ config")
except Exception as e:
    print(f"  ❌ config: {e}")
    errors.append(("config", e))

try:
    from src.catchup.core import models
    print("  ✅ models")
except Exception as e:
    print(f"  ❌ models: {e}")
    errors.append(("models", e))

try:
    from src.catchup.core import parsing
    print("  ✅ parsing")
except Exception as e:
    print(f"  ❌ parsing: {e}")
    errors.append(("parsing", e))

try:
    from src.catchup.core import rendering
    print("  ✅ rendering")
except Exception as e:
    print(f"  ❌ rendering: {e}")
    errors.append(("rendering", e))

# Database
print("\nChecking database...")
try:
    from src.catchup.db import database
    print("  ✅ database")
except Exception as e:
    print(f"  ❌ database: {e}")
    errors.append(("database", e))

# Clients
print("\nChecking clients...")
try:
    from src.catchup.clients import metadata
    print("  ✅ metadata")
except Exception as e:
    print(f"  ❌ metadata: {e}")
    errors.append(("metadata", e))

try:
    from src.catchup.clients import downloader
    print("  ✅ downloader")
except Exception as e:
    print(f"  ❌ downloader: {e}")
    errors.append(("downloader", e))

try:
    from src.catchup.clients import converter
    print("  ✅ converter")
except Exception as e:
    print(f"  ❌ converter: {e}")
    errors.append(("converter", e))

try:
    from src.catchup.clients import transcriber
    print("  ✅ transcriber")
except Exception as e:
    print(f"  ❌ transcriber: {e}")
    errors.append(("transcriber", e))

try:
    from src.catchup.clients import summarizer
    print("  ✅ summarizer")
except Exception as e:
    print(f"  ❌ summarizer: {e}")
    errors.append(("summarizer", e))

# Pipeline (skip vad as it requires torch)
print("\nChecking pipeline...")
try:
    from src.catchup.pipeline import interfaces
    print("  ✅ interfaces")
except Exception as e:
    print(f"  ❌ interfaces: {e}")
    errors.append(("interfaces", e))

try:
    from src.catchup.pipeline import runner
    print("  ✅ runner")
except Exception as e:
    print(f"  ❌ runner: {e}")
    errors.append(("runner", e))

try:
    from src.catchup.pipeline import fake_clients
    print("  ✅ fake_clients")
except Exception as e:
    print(f"  ❌ fake_clients: {e}")
    errors.append(("fake_clients", e))

try:
    from src.catchup.pipeline import factory
    print("  ✅ factory")
except Exception as e:
    print(f"  ❌ factory: {e}")
    errors.append(("factory", e))

# API
print("\nChecking API...")
try:
    from src.catchup.api import main
    print("  ✅ main")
except Exception as e:
    print(f"  ❌ main: {e}")
    errors.append(("main", e))

# Summary
print("\n" + "="*60)
if errors:
    print(f"❌ {len(errors)} import error(s) found:")
    for module, error in errors:
        print(f"   - {module}: {error}")
    sys.exit(1)
else:
    print("✅ All imports successful!")
    sys.exit(0)
