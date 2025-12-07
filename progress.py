"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous coding agent.
"""

import json
from pathlib import Path


def count_passing_tests(project_dir: Path) -> tuple[int, int]:
    """
    Count passing and total tests in feature_list.json.

    Args:
        project_dir: Directory containing feature_list.json

    Returns:
        (passing_count, total_count)
    """
    tests_file = project_dir / "feature_list.json"

    if not tests_file.exists():
        return 0, 0

    try:
        with open(tests_file, "r") as f:
            tests = json.load(f)

        total = len(tests)
        passing = sum(1 for test in tests if test.get("passes", False))

        return passing, total
    except (json.JSONDecodeError, IOError):
        return 0, 0


def is_work_complete(project_dir: Path) -> bool:
    """
    Check if all features in feature_list.json are passing.
    
    Args:
        project_dir: Directory containing feature_list.json
        
    Returns:
        True if all features pass OR if feature list is empty (no work to do),
        False if file doesn't exist or if there are failing features
    """
    tests_file = project_dir / "feature_list.json"
    
    # If file doesn't exist, work is not complete (initializer needs to run)
    if not tests_file.exists():
        return False
    
    try:
        with open(tests_file, "r") as f:
            tests = json.load(f)
        
        total = len(tests)
        passing = sum(1 for test in tests if test.get("passes", False))
        
        # If feature list is empty, there's no work to do - consider it complete
        if total == 0:
            return True
        
        # Work is complete when all tests pass
        return passing == total
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, work is not complete
        return False


def print_session_header(session_num: int, is_initializer: bool) -> None:
    """Print a formatted header for the session."""
    session_type = "INITIALIZER" if is_initializer else "CODING AGENT"

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {session_type}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path) -> None:
    """Print a summary of current progress."""
    passing, total = count_passing_tests(project_dir)

    if total > 0:
        percentage = (passing / total) * 100
        print(f"\nProgress: {passing}/{total} tests passing ({percentage:.1f}%)")
    else:
        print("\nProgress: feature_list.json not yet created")
