import subprocess
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.getcwd())
from speccheck import __version__

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_docker_commands():
    try:
        # Run docker login
        subprocess.run(["docker", "login"], check=True)
        
        # Run docker build
        logger.info("Building docker image happykhan/speccheck:%s", __version__)
        subprocess.run([
            "docker", "build", 
            "--platform", "linux/amd64", 
            "-t", f"happykhan/speccheck:{__version__}", 
            "-f", "docker/Dockerfile", 
            "."
        ], check=True)
        
        # Run docker push
        subprocess.run(["docker", "push", f"happykhan/speccheck:{__version__}"], check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error("An error occurred: %s", e)

if __name__ == "__main__":
    run_docker_commands()