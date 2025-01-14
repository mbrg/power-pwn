import os
import subprocess  # nosec
import sys


def log(message: str) -> None:
    print(f"[init_repo] {message}")


def check_python_version() -> bool:
    """
    Check if the current Python version is between 3.6 and 3.8 inclusive.
    """
    version_info = sys.version_info
    if version_info.major != 3:
        return False
    if version_info.minor < 6 or version_info.minor > 8:
        return False
    return True


def find_python() -> str:
    """
    Get the path of the currently running Python executable.
    """
    return sys.executable


def main() -> None:
    if not check_python_version():
        log("Error: Supported Python versions are between 3.6 and 3.8.")
        log(f"Detected Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        sys.exit(1)

    python_executable = find_python()
    log(f"Using Python executable: {python_executable}")

    log("Creating virtual environment")
    subprocess.run(f"{python_executable} -m venv .venv", shell=True)  # nosec

    log("Installing Python packages")
    py_path = os.path.join(".venv", "bin", "python")

    if sys.platform.startswith("win"):
        py_path = os.path.join(".venv", "Scripts", "python")

    subprocess.run(f"{py_path} -m pip install --upgrade pip", shell=True)  # nosec

    # Install packages from requirements.txt
    subprocess.run(f"{py_path} -m pip install -r requirements.txt", shell=True)  # nosec

    log("Python packages installed successfully")
    log("DONE!")


if __name__ == "__main__":
    main()
