#!/usr/bin/env python3
"""Check Python syntax without importing (no dependencies needed)."""
import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

# Find all Python files
src_dir = Path(__file__).parent / "src"
test_dir = Path(__file__).parent / "tests"

python_files = list(src_dir.rglob("*.py")) + list(test_dir.rglob("*.py"))

print(f"🔍 Checking syntax of {len(python_files)} Python files...\n")

errors = []
for file_path in sorted(python_files):
    relative_path = file_path.relative_to(Path(__file__).parent)
    success, error = check_syntax(file_path)

    if success:
        print(f"  ✅ {relative_path}")
    else:
        print(f"  ❌ {relative_path}: {error}")
        errors.append((relative_path, error))

print("\n" + "="*60)
if errors:
    print(f"❌ {len(errors)} syntax error(s) found:")
    for path, error in errors:
        print(f"   - {path}: {error}")
    sys.exit(1)
else:
    print(f"✅ All {len(python_files)} files have valid syntax!")
    sys.exit(0)
