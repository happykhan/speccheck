import logging
import os
import shutil
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.getcwd())
import argparse

from speccheck import __version__

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def find_docker_executable():
    """Find the docker executable in common locations."""
    # First try shutil.which with expanded PATH
    docker_path = shutil.which('docker')
    if docker_path:
        return docker_path

    # Check common macOS locations
    common_paths = [
        '/usr/local/bin/docker',
        '/opt/homebrew/bin/docker',
        '/Applications/Docker.app/Contents/Resources/bin/docker',
        '/Applications/OrbStack.app/Contents/MacOS/xbin/docker'
    ]

    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            logger.info("Found Docker at: %s", path)
            return path

    logger.error("Docker executable not found. Please install Docker Desktop or OrbStack.")
    logger.error("Checked locations:")
    for path in common_paths:
        logger.error("  - %s", path)
    sys.exit(1)

def get_docker_env():
    """Get environment with Docker credential helper in PATH."""
    env = os.environ.copy()

    # Add common credential helper locations to PATH
    credential_paths = [
        '/Applications/OrbStack.app/Contents/MacOS/xbin',
        '/Applications/Docker.app/Contents/Resources/bin',
        '/usr/local/bin',
        '/opt/homebrew/bin'
    ]

    current_path = env.get('PATH', '')
    new_paths = [p for p in credential_paths if os.path.exists(p)]

    if new_paths:
        env['PATH'] = ':'.join(new_paths + [current_path])

    return env

def check_required_files():
    """Check if all required files exist before building."""
    required_files = [
        'pyproject.toml',
        'README.md',
        'LICENSE',
        'criteria.csv',
        'speccheck/__init__.py',
        'templates/report.html',
        'docker/Dockerfile'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            logger.info("✓ Found: %s", file)

    if missing_files:
        logger.error("Missing required files:")
        for file in missing_files:
            logger.error("  ✗ %s", file)
        return False

    return True

def run_docker_commands():
    try:
        # Find Docker executable
        docker_cmd = find_docker_executable()
        docker_env = get_docker_env()
        logger.info("")

        # Check required files
        logger.info("Checking required files...")
        if not check_required_files():
            logger.error("Build aborted due to missing files")
            sys.exit(1)

        logger.info("")

        # Check if already logged in to Docker
        try:
            result = subprocess.run(
                [docker_cmd, "info"],
                capture_output=True,
                text=True,
                check=True,
                env=docker_env
            )
            if "Username:" in result.stdout:
                logger.info("Already logged in to Docker")
            else:
                logger.info("Running docker login...")
                subprocess.run([docker_cmd, "login"], check=True, env=docker_env)
        except subprocess.CalledProcessError:
            logger.info("Running docker login...")
            subprocess.run([docker_cmd, "login"], check=True, env=docker_env)

        logger.info("")

        # Run docker build
        image_name = f"happykhan/speccheck:{__version__}"
        logger.info("Building docker image: %s", image_name)
        logger.info("Platform: linux/amd64")
        logger.info("")

        subprocess.run([
            docker_cmd, "build",
            "--platform", "linux/amd64",
            "-t", image_name,
            "-f", "docker/Dockerfile",
            "."
        ], check=True, env=docker_env)

        logger.info("")
        logger.info("✓ Build successful!")
        logger.info("")

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--push', action='store_true', help='Automatically push image to Docker Hub', default=True)
        args, _ = parser.parse_known_args()

        if args.push:
            logger.info("Auto-pushing to Docker Hub (--push)...")
            subprocess.run([docker_cmd, "push", image_name], check=True, env=docker_env)
            logger.info("✓ Push successful!")
        else:
            logger.info("Push skipped.")
            logger.info("")
            logger.info("To push manually:")
            logger.info("  docker push %s", image_name)

    except subprocess.CalledProcessError as e:
        logger.error("An error occurred: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nBuild cancelled by user")
        sys.exit(0)


if __name__ == "__main__":
    run_docker_commands()
