#!/usr/bin/env python3
"""
Version bumping utility for speccheck.

Updates version in both __init__.py and pyproject.toml to keep them in sync.

Usage:
    python bump_version.py 1.0.1
    python bump_version.py --major  # 1.0.0 -> 2.0.0
    python bump_version.py --minor  # 1.0.0 -> 1.1.0
    python bump_version.py --patch  # 1.0.0 -> 1.0.1
"""

import argparse
import re
import sys
from pathlib import Path


def get_current_version(init_file: Path) -> str:
    """Extract current version from __init__.py"""
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find __version__ in __init__.py")
    return match.group(1)


def bump_version(version: str, bump_type: str) -> str:
    """Bump version number based on type (major, minor, patch)"""
    major, minor, patch = map(int, version.split('.'))
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """Update version string in a file"""
    content = file_path.read_text()
    
    if file_path.name == '__init__.py':
        pattern = r'(__version__\s*=\s*["\'])([^"\']+)(["\'])'
        updated = re.sub(pattern, rf'\g<1>{new_version}\g<3>', content)
    elif file_path.name == 'pyproject.toml':
        pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
        updated = re.sub(pattern, rf'\g<1>{new_version}\g<3>', content)
    else:
        raise ValueError(f"Unknown file type: {file_path.name}")
    
    if updated == content:
        raise ValueError(f"Failed to update version in {file_path}")
    
    file_path.write_text(updated)
    print(f"✓ Updated {file_path.name}: {old_version} → {new_version}")


def main():
    parser = argparse.ArgumentParser(description='Bump version in __init__.py and pyproject.toml')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('version', nargs='?', help='Explicit version number (e.g., 1.0.1)')
    group.add_argument('--major', action='store_true', help='Bump major version (X.0.0)')
    group.add_argument('--minor', action='store_true', help='Bump minor version (x.X.0)')
    group.add_argument('--patch', action='store_true', help='Bump patch version (x.x.X)')
    
    args = parser.parse_args()
    
    # File paths
    root_dir = Path(__file__).parent
    init_file = root_dir / 'speccheck' / '__init__.py'
    pyproject_file = root_dir / 'pyproject.toml'
    
    # Validate files exist
    if not init_file.exists():
        print(f"Error: {init_file} not found", file=sys.stderr)
        sys.exit(1)
    if not pyproject_file.exists():
        print(f"Error: {pyproject_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version(init_file)
    print(f"Current version: {current_version}")
    
    # Determine new version
    if args.version:
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+$', args.version):
            print("Error: Version must be in format X.Y.Z (e.g., 1.0.1)", file=sys.stderr)
            sys.exit(1)
        new_version = args.version
    else:
        # Auto-bump based on flag
        if args.major:
            bump_type = 'major'
        elif args.minor:
            bump_type = 'minor'
        elif args.patch:
            bump_type = 'patch'
        new_version = bump_version(current_version, bump_type)
    
    print(f"New version: {new_version}")
    
    # Confirm
    response = input(f"\nUpdate version to {new_version}? [y/N] ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    # Update files
    try:
        update_version_in_file(init_file, current_version, new_version)
        update_version_in_file(pyproject_file, current_version, new_version)
        print(f"\n✓ Successfully updated version to {new_version}")
        print("\nNext steps:")
        print("  1. git add speccheck/__init__.py pyproject.toml")
        print(f"  2. git commit -m 'Bump version to {new_version}'")
        print(f"  3. git tag v{new_version}")
        print("  4. git push && git push --tags")
        print("  5. python -m build")
        print("  6. twine upload dist/*")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
