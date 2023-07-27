import os
import subprocess  # nosec
import sys


def log(message: str) -> None:
    print(f"[init_repo] {message}")


def check_python_version() -> bool:
    version_info = sys.version_info
    if version_info.major != 3:
        return False
    if version_info.minor < 6 or version_info.minor > 8:
        return False

    return True


def main() -> None:
    if check_python_version():
        log("Creating virtual environment")
        subprocess.run("python -m venv .venv")  # nosec

        log("Installing python packages")
        py_path = os.path.join(".venv", "Scripts", "python")

        if not sys.platform.startswith("win"):
            py_path = os.path.join(".venv", "bin", "python")

        subprocess.run(f"{py_path} -m pip install --upgrade pip", shell=True)  # nosec

        # install packages
        subprocess.run(f"{py_path} -m pip install -r requirements.txt", shell=True)  # nosec

        log("Python packages installed successfully")

        log("DONE!")

    else:
        log("Supported python versions are 3.6-3.8")


if __name__ == "__main__":
    main()
