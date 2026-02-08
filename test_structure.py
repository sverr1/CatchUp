#!/usr/bin/env python3
"""Test project structure and configuration."""
import sys
from pathlib import Path

def test_directory_structure():
    """Verify all required directories exist."""
    print("Testing directory structure...")
    required_dirs = [
        "src/catchup/api",
        "src/catchup/core",
        "src/catchup/db",
        "src/catchup/clients",
        "src/catchup/pipeline",
        "tests/unit",
        "tests/integration",
        "tests/live",
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            missing.append(dir_path)
            print(f"  ❌ Missing: {dir_path}")
        else:
            print(f"  ✅ {dir_path}")

    if missing:
        print(f"\n❌ {len(missing)} directories missing!")
        return False
    else:
        print(f"  ✅ All {len(required_dirs)} directories exist")
        return True

def test_required_files():
    """Verify all required files exist."""
    print("\nTesting required files...")
    required_files = [
        "requirements.txt",
        "requirements-minimal.txt",
        "requirements-ml.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "plan.md",
        "pytest.ini",
        "main.py",
        "src/catchup/__init__.py",
        "src/catchup/core/config.py",
        "src/catchup/core/models.py",
        "src/catchup/core/parsing.py",
        "src/catchup/core/rendering.py",
        "src/catchup/db/database.py",
        "src/catchup/clients/metadata.py",
        "src/catchup/clients/downloader.py",
        "src/catchup/clients/converter.py",
        "src/catchup/clients/vad.py",
        "src/catchup/clients/transcriber.py",
        "src/catchup/clients/summarizer.py",
        "src/catchup/pipeline/interfaces.py",
        "src/catchup/pipeline/runner.py",
        "src/catchup/pipeline/fake_clients.py",
        "src/catchup/pipeline/factory.py",
        "src/catchup/api/main.py",
        "src/catchup/api/static/index.html",
        "tests/conftest.py",
        "tests/utils.py",
        "tests/unit/test_parsing.py",
    ]

    missing = []
    for file_path in required_files:
        full_path = Path(file_path)
        if not full_path.exists():
            missing.append(file_path)
            print(f"  ❌ Missing: {file_path}")

    if missing:
        print(f"\n❌ {len(missing)} files missing!")
        for f in missing:
            print(f"   - {f}")
        return False
    else:
        print(f"  ✅ All {len(required_files)} required files exist")
        return True

def test_env_example():
    """Verify .env.example has required keys."""
    print("\nTesting .env.example...")
    required_keys = [
        "MISTRAL_API_KEY",
        "DATA_DIR",
        "SQLITE_PATH",
        "LONG_SILENCE_SEC",
        "KEEP_SILENCE_SEC",
        "PADDING_SEC",
        "CHUNK_MINUTES",
        "CHUNK_OVERLAP_SEC",
        "HOST",
        "PORT",
        "USE_FAKE_CLIENTS",
    ]

    env_path = Path(".env.example")
    if not env_path.exists():
        print("  ❌ .env.example not found!")
        return False

    content = env_path.read_text()
    missing_keys = []

    for key in required_keys:
        if key not in content:
            missing_keys.append(key)
            print(f"  ❌ Missing key: {key}")
        else:
            print(f"  ✅ {key}")

    if missing_keys:
        print(f"\n❌ {len(missing_keys)} keys missing from .env.example!")
        return False
    else:
        print(f"  ✅ All {len(required_keys)} configuration keys present")
        return True

def main():
    """Run all structure tests."""
    print("🏗️  Testing project structure...\n")
    print("="*60)

    results = []
    results.append(("Directory structure", test_directory_structure()))
    print("\n" + "="*60)
    results.append(("Required files", test_required_files()))
    print("\n" + "="*60)
    results.append(("Configuration", test_env_example()))

    print("\n" + "="*60)
    print("\n📊 SUMMARY\n")

    failed = [name for name, passed in results if not passed]

    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")

    print("\n" + "="*60)

    if failed:
        print(f"\n❌ {len(failed)} test(s) failed!")
        return 1
    else:
        print(f"\n✅ All structure tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
