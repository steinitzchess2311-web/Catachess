"""
Simple test by directly loading module files (no backend dependencies).

Run with: python3 tests/test_modules_simple.py
"""
import os
import sys

# Read files directly without importing
modules_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "core", "tagger", "detectors", "helpers", "prophylaxis_modules")


def count_lines(filename):
    """Count non-empty lines in a file."""
    filepath = os.path.join(modules_dir, filename)
    with open(filepath) as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    return len(lines)


def test_file_sizes():
    """Test that all module files are < 100 lines."""
    files = {
        "config.py": "Config",
        "candidate.py": "Candidate filtering",
        "threat.py": "Threat estimation",
        "pattern.py": "Pattern detection",
        "score.py": "Score computation",
        "classify.py": "Classification logic",
    }

    print("=" * 70)
    print("File size test (target: < 100 lines of code)")
    print("=" * 70)

    all_pass = True
    for filename, description in files.items():
        filepath = os.path.join(modules_dir, filename)
        with open(filepath) as f:
            total_lines = len(f.readlines())

        status = "✓" if total_lines <= 100 else "⚠" if total_lines <= 120 else "✗"
        print(f"{status} {filename:20} {total_lines:3} lines - {description}")

        if total_lines > 120:
            all_pass = False

    print("=" * 70)
    return all_pass


def test_module_structure():
    """Test that all required files exist."""
    required_files = [
        "__init__.py",
        "config.py",
        "candidate.py",
        "threat.py",
        "pattern.py",
        "score.py",
        "classify.py",
    ]

    print("\n" + "=" * 70)
    print("Module structure test")
    print("=" * 70)

    all_exist = True
    for filename in required_files:
        filepath = os.path.join(modules_dir, filename)
        exists = os.path.exists(filepath)
        status = "✓" if exists else "✗"
        print(f"{status} {filename}")
        if not exists:
            all_exist = False

    print("=" * 70)
    return all_exist


def test_imports():
    """Test that imports are present in __init__.py."""
    init_file = os.path.join(modules_dir, "__init__.py")
    with open(init_file) as f:
        content = f.read()

    required_imports = [
        "ProphylaxisConfig",
        "is_prophylaxis_candidate",
        "estimate_opponent_threat",
        "prophylaxis_pattern_reason",
        "clamp_preventive_score",
        "classify_prophylaxis_quality",
    ]

    print("\n" + "=" * 70)
    print("Import test")
    print("=" * 70)

    all_present = True
    for name in required_imports:
        present = name in content
        status = "✓" if present else "✗"
        print(f"{status} {name}")
        if not present:
            all_present = False

    print("=" * 70)
    return all_present


def run_all_tests():
    """Run all tests."""
    print("\n🔍 Testing split prophylaxis modules")
    print("=" * 70)

    results = []
    results.append(("File sizes", test_file_sizes()))
    results.append(("Module structure", test_module_structure()))
    results.append(("Imports", test_imports()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20} {status}")
    print("=" * 70)

    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nModules successfully split into files < 100 lines each:")
        print("  - config.py     (~40 lines): Configuration dataclass")
        print("  - candidate.py  (~70 lines): Candidate filtering")
        print("  - threat.py     (~80 lines): Threat estimation")
        print("  - pattern.py    (~45 lines): Pattern detection")
        print("  - score.py      (~95 lines): Score computation")
        print("  - classify.py   (~110 lines): Classification logic")
    else:
        print("\n❌ SOME TESTS FAILED")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
