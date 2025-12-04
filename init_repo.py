import os
import platform
import subprocess  # nosec
import sys
from shutil import which


def log(message: str) -> None:
    print(f"[init_repo] {message}")


def log_section(message: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {message}")
    print(f"{'=' * 70}\n")


def check_python_version() -> bool:
    """
    Check if the current Python version is 3.11.
    """
    version_info = sys.version_info
    if version_info.major != 3:
        return False
    if version_info.minor != 11:
        return False
    return True


def find_python() -> str:
    """
    Get the path of the currently running Python executable.
    """
    return sys.executable


def get_os() -> str:
    """
    Detect the operating system.
    Returns: 'macos', 'linux', or 'windows'
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    return "unknown"


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return which(command) is not None


def install_nodejs(os_type: str) -> bool:
    """Install Node.js based on OS."""
    log_section("Installing Node.js")

    if command_exists("node"):
        node_version = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
        log(f"✓ Node.js already installed: {node_version}")
        return True

    try:
        if os_type == "macos":
            log("Installing Node.js via Homebrew...")
            subprocess.run("brew install node", shell=True, check=True)  # nosec
        elif os_type == "linux":
            log("Installing Node.js via apt...")
            subprocess.run("sudo apt-get update", shell=True, check=True)  # nosec
            subprocess.run("sudo apt-get install -y nodejs npm", shell=True, check=True)  # nosec
        elif os_type == "windows":
            log("❌ Automated Node.js installation not supported on Windows")
            log("Please install Node.js manually from: https://nodejs.org/")
            return False

        if command_exists("node"):
            node_version = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
            log(f"✅ Node.js installed successfully: {node_version}")
            return True
        else:
            log("❌ Node.js installation failed")
            return False

    except subprocess.CalledProcessError as e:
        log(f"❌ Error installing Node.js: {e}")
        return False


def install_ffuf(os_type: str) -> bool:
    """Install ffuf based on OS."""
    log_section("Installing ffuf")

    if command_exists("ffuf"):
        log("✓ ffuf already installed")
        return True

    try:
        if os_type == "macos":
            log("Installing ffuf via Homebrew...")
            subprocess.run("brew install ffuf", shell=True, check=True)  # nosec
        elif os_type == "linux":
            log("Installing ffuf from GitHub releases...")
            arch = platform.machine().lower()
            if "x86_64" in arch or "amd64" in arch:
                ffuf_arch = "amd64"
            elif "arm64" in arch or "aarch64" in arch:
                ffuf_arch = "arm64"
            else:
                log(f"❌ Unsupported architecture: {arch}")
                return False

            commands = [
                f"wget -q https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_{ffuf_arch}.tar.gz",
                f"tar -xzf ffuf_2.1.0_linux_{ffuf_arch}.tar.gz ffuf",
                f"rm -f ffuf_2.1.0_linux_{ffuf_arch}.tar.gz",
                "sudo mv ffuf /usr/local/bin/ffuf",
                "sudo chmod +x /usr/local/bin/ffuf",
            ]
            for cmd in commands:
                subprocess.run(cmd, shell=True, check=True)  # nosec
        elif os_type == "windows":
            log("❌ Automated ffuf installation not supported on Windows")
            log("Please install ffuf manually from: https://github.com/ffuf/ffuf/releases")
            return False

        if command_exists("ffuf"):
            log("✅ ffuf installed successfully")
            return True
        else:
            log("❌ ffuf installation failed")
            return False

    except subprocess.CalledProcessError as e:
        log(f"❌ Error installing ffuf: {e}")
        return False


def install_subfinder(os_type: str) -> bool:
    """Install subfinder based on OS."""
    log_section("Installing subfinder")

    if command_exists("subfinder"):
        log("✓ subfinder already installed")
        return True

    try:
        if os_type == "macos":
            log("Installing subfinder via Homebrew...")
            subprocess.run("brew install subfinder", shell=True, check=True)  # nosec
        elif os_type == "linux":
            if not command_exists("go"):
                log("❌ Go is not installed. subfinder requires Go.")
                log("Please install Go first: https://golang.org/doc/install")
                return False
            log("Installing subfinder via Go...")
            subprocess.run("go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest", shell=True, check=True)  # nosec
            log("Note: Make sure $GOPATH/bin or ~/go/bin is in your PATH")
        elif os_type == "windows":
            if not command_exists("go"):
                log("❌ Go is not installed. subfinder requires Go.")
                log("Please install Go first: https://golang.org/doc/install")
                return False
            log("Installing subfinder via Go...")
            subprocess.run("go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest", shell=True, check=True)  # nosec
            log("Note: Make sure %GOPATH%\\bin or %USERPROFILE%\\go\\bin is in your PATH")

        if command_exists("subfinder"):
            log("✅ subfinder installed successfully")
            return True
        else:
            log("❌ subfinder installation failed")
            log("If using Go install, make sure your Go bin directory is in PATH")
            return False

    except subprocess.CalledProcessError as e:
        log(f"❌ Error installing subfinder: {e}")
        return False


def install_node_packages() -> bool:
    """Install Node.js packages for all modules."""
    log_section("Installing Node.js Packages")

    if not command_exists("npm"):
        log("❌ npm not found. Please install Node.js first.")
        return False

    packages_installed = True

    # List of directories with package.json
    package_dirs = [
        "src/powerpwn/custom_gpt_hunter",
        "src/powerpwn/agent_builder",
        "src/powerpwn/copilot_studio/tools/pup_query_webchat",
        "src/powerpwn/copilot_studio/tools/pup_is_webchat_live",
    ]

    for package_dir in package_dirs:
        if not os.path.exists(package_dir):
            continue

        log(f"Installing packages in {package_dir}...")
        try:
            result = subprocess.run("npm install", shell=True, cwd=package_dir, capture_output=True, text=True, timeout=300)  # nosec

            if result.returncode == 0:
                log(f"✅ Packages installed in {package_dir}")
            else:
                log(f"❌ Failed to install packages in {package_dir}")
                log(f"   Error: {result.stderr}")
                packages_installed = False
        except subprocess.TimeoutExpired:
            log(f"❌ npm install timed out in {package_dir}")
            packages_installed = False
        except Exception as e:
            log(f"❌ Error installing packages in {package_dir}: {e}")
            packages_installed = False

    return packages_installed


def install_external_tools(os_type: str) -> bool:
    """Install all external tools."""
    log_section("Installing External Tools")
    log(f"Detected OS: {os_type}")

    if os_type == "unknown":
        log("❌ Unsupported operating system")
        return False

    if os_type == "windows":
        log("")
        log("⚠️  Automated installation not fully supported on Windows")
        log("Please install the following tools manually:")
        log("  - Node.js: https://nodejs.org/")
        log("  - ffuf: https://github.com/ffuf/ffuf/releases")
        log("  - subfinder: https://github.com/projectdiscovery/subfinder")
        log("")
        return False

    # Install tools
    nodejs_ok = install_nodejs(os_type)
    ffuf_ok = install_ffuf(os_type)
    subfinder_ok = install_subfinder(os_type)

    # Install Node packages if Node.js is available
    packages_ok = True
    if nodejs_ok:
        packages_ok = install_node_packages()

    # Summary
    log_section("Installation Summary")
    log(f"Node.js:   {'✅' if nodejs_ok else '❌'}")
    log(f"ffuf:      {'✅' if ffuf_ok else '❌'}")
    log(f"subfinder: {'✅' if subfinder_ok else '❌'}")
    log(f"Packages:  {'✅' if packages_ok else '❌'}")

    return nodejs_ok and ffuf_ok and subfinder_ok and packages_ok


def main() -> None:
    # Parse command line arguments
    install_external = "--install-external-tools" in sys.argv

    if not check_python_version():
        log("Error: Supported Python version is 3.11.")
        log(f"Detected Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        sys.exit(1)

    # Install external tools if requested
    if install_external:
        os_type = get_os()
        if not install_external_tools(os_type):
            log("")
            log("⚠️  Some external tools failed to install")
            log("You can continue with Python setup, but some features may not work")
            log("")

    python_executable = find_python()
    log(f"Using Python executable: {python_executable}")

    log_section("Setting up Python Environment")

    log("Creating virtual environment")
    subprocess.run(f"{python_executable} -m venv .venv", shell=True)  # nosec

    log("Installing Python packages")
    py_path = os.path.join(".venv", "bin", "python")

    if sys.platform.startswith("win"):
        py_path = os.path.join(".venv", "Scripts", "python")

    subprocess.run(f"{py_path} -m pip install --upgrade pip", shell=True)  # nosec

    # Install packages from requirements.txt
    subprocess.run(f"{py_path} -m pip install -r requirements.txt", shell=True)  # nosec

    log("Installing package in editable mode")
    subprocess.run(f"{py_path} -m pip install -e .", shell=True)  # nosec

    log("Python packages installed successfully")

    log_section("Setup Complete!")
    log("")
    log("To use the virtual environment, run:")
    log("  source .venv/bin/activate")
    log("")
    log("Then you can run commands like:")
    log("  powerpwn --help")
    log("")

    if not install_external:
        log("=" * 70)
        log("Optional: Install external tools (ffuf, subfinder, Node.js)")
        log("Run: python init_repo.py --install-external-tools")
        log("=" * 70)
        log("")
        log("Or install module-specific dependencies:")
        log("  custom-gpt-hunter:  ./src/powerpwn/custom_gpt_hunter/install_dependencies.sh")
        log("  agent-builder:      ./src/powerpwn/agent_builder/install_dependencies.sh")
        log("  copilot-studio:     ./src/powerpwn/copilot_studio/install_dependencies.sh")

    log("=" * 70)


if __name__ == "__main__":
    main()
