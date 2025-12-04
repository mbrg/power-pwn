#!/usr/bin/env python3
"""
Progressive ffuf scanner for discovering AI agent/chatbot deployments.

Scans multiple endpoints with FUZZ keyword replacement to discover vercel-hosted agents.
Features:
    - Tracks progress per endpoint and resumes from where it left off
    - Press Ctrl+C to stop gracefully (saves progress/results)
    - Combined output file for all endpoints
    - Configurable timeout behavior
"""

import logging
import re
import select
import subprocess  # nosec B404 - Required for security toolset to execute external tools
import sys
import time
from pathlib import Path
from typing import List, Optional, Set

from powerpwn.cli.const import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"


class ProgressiveFFUF:
    """
    Progressive ffuf scanner that pauses periodically and resumes.
    Keeps original ffuf_progressive.py logic intact for stability.
    """

    def __init__(
        self,
        wordlist_path: str,
        target_url: str,
        output_file: str,
        progress_file: str,
        endpoint_name: str = "",
        run_duration: int = 20,
        pause_duration: int = 15,
        rate: int = 40,
        threads: int = 10,
        filter_codes: str = "404,403",
    ):
        self.wordlist_path = Path(wordlist_path)
        self.target_url = target_url
        self.output_file = Path(output_file)
        self.endpoint_name = endpoint_name
        self.run_duration = run_duration
        self.pause_duration = pause_duration
        self.rate = rate
        self.threads = threads
        self.filter_codes = filter_codes

        # Progress tracking
        self.progress_file = Path(progress_file)
        self.temp_wordlist = Path(f"{wordlist_path}.temp_{int(time.time())}")
        self.current_line = self.load_progress()
        self.total_lines = self.count_wordlist_lines()

        # Found URLs tracking
        self.found_urls: Set[str] = set()
        self.requests_made_in_cycle = 0

    def count_wordlist_lines(self) -> int:
        """Count total lines in wordlist."""
        with open(self.wordlist_path, "r") as f:
            return sum(1 for _ in f)

    def load_progress(self) -> int:
        """Load progress from file or start from 0."""
        if self.progress_file.exists():
            with open(self.progress_file, "r") as f:
                return int(f.read().strip())
        return 0

    def save_progress(self) -> None:
        """Save current progress."""
        with open(self.progress_file, "w") as f:
            f.write(str(self.current_line))

    def create_temp_wordlist(self) -> None:
        """Create a temporary wordlist starting from current position."""
        with open(self.wordlist_path, "r") as infile:
            with open(self.temp_wordlist, "w") as outfile:
                for i, line in enumerate(infile):
                    if i >= self.current_line:
                        outfile.write(line)

    def parse_ffuf_output_for_url(self, line: str) -> Optional[str]:
        """Parse ffuf output line and extract URL if match."""
        # ffuf output shows URL when there's a hit
        # Look for lines with successful responses
        if "Status:" in line and "Size:" in line:
            # Extract URL from the beginning of the line
            url_match = re.match(r"^(https?://[^\s\[]+)", line.strip())
            if url_match:
                return url_match.group(1)
        return None

    def parse_ffuf_progress(self, line: str) -> Optional[int]:
        """Parse ffuf progress to get current request number."""
        # ffuf shows: ":: Progress: [1234/5678] ::"
        progress_match = re.search(r"Progress:\s*\[(\d+)/\d+\]", line)
        if progress_match:
            return int(progress_match.group(1))
        return None

    def _parse_ffuf_csv(self, csv_file: Path) -> None:
        """Parse ffuf CSV output and extract URLs."""
        import csv

        try:
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # CSV has columns: url, position, status_code, etc.
                    if "url" in row and row["url"]:
                        url = row["url"].strip()
                        self.found_urls.add(url)
                        logger.info(f"{COLOR_GREEN}✓ Found: {url}{COLOR_RESET}")
        except Exception as e:
            logger.warning(f"Could not parse CSV: {e}")

    def save_found_urls_to_file(self) -> None:
        """Save found URLs to output file (URLs only, no comments)."""
        if not self.found_urls:
            return

        # Read existing URLs to avoid duplicates
        existing_urls = set()
        if self.output_file.exists():
            with open(self.output_file, "r") as f:
                existing_urls = {line.strip() for line in f if line.strip()}

        # Find new URLs
        new_urls = self.found_urls - existing_urls

        if new_urls:
            with open(self.output_file, "a") as f:
                for url in sorted(new_urls):
                    f.write(f"{url}\n")

            logger.info(f"Saved {len(new_urls)} new URL(s) to {self.output_file}")
        else:
            logger.info("No new URLs to save")

    def run_ffuf_cycle(self) -> bool:
        """Run one ffuf cycle. Returns True if completed."""
        pct = self.current_line / self.total_lines * 100
        progress = f"Progress: {self.current_line:,} / {self.total_lines:,} lines ({pct:.1f}%)"
        logger.info(f"{'='*60}")
        logger.info(progress)
        logger.info(f"Running ffuf for {self.run_duration} seconds...")
        logger.info(f"{'='*60}")

        # Reset cycle tracking
        self.requests_made_in_cycle = 0
        cycle_start_line = self.current_line

        # Create temporary wordlist from current position
        self.create_temp_wordlist()

        # Create temporary output file for this cycle
        temp_output = Path(f".ffuf_temp_{int(time.time())}.csv")

        # Build ffuf command with CSV output for reliable parsing
        cmd = [
            "ffuf",
            "-s",
            "-w",
            f"{self.temp_wordlist}:FUZZ",
            "-u",
            self.target_url,
            "-fc",
            self.filter_codes,
            "-rate",
            str(self.rate),
            "-t",
            str(self.threads),
            "-se",  # Stop on spurious errors
            "-ac",  # Auto-calibrate
            "-of",
            "csv",
            "-o",
            str(temp_output),
        ]

        try:
            # Start ffuf process - redirect stderr to DEVNULL to suppress calibration errors
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
            )  # nosec B603 - Controlled command list, security tool requirement

            # Monitor output in real-time
            start_time = time.time()

            while True:
                # Check if time limit reached
                if time.time() - start_time >= self.run_duration:
                    logger.info("Time limit reached. Stopping ffuf...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    break

                # Check if process completed naturally
                if process.poll() is not None:
                    # Read any remaining output
                    remaining = process.stdout.read() if process.stdout else ""
                    if remaining:
                        print(remaining, end="")
                    break

                # Use select to check if data is available (non-blocking)
                # Only works on Unix-like systems
                if process.stdout:
                    ready, _, _ = select.select([process.stdout], [], [], 0.1)
                    if ready:
                        line = process.stdout.readline()
                        if line:
                            # Track progress from ffuf output
                            progress_num = self.parse_ffuf_progress(line)
                            if progress_num:
                                self.requests_made_in_cycle = progress_num

                            # Print the line
                            print(line, end="")
                    else:
                        # No data available, small delay to avoid CPU spinning
                        time.sleep(0.01)

                # Parse the CSV output file to extract URLs
            if temp_output.exists():
                num_found_in_cycle = len(self.found_urls)
                self._parse_ffuf_csv(temp_output)
                temp_output.unlink()  # Clean up temp CSV
                # Show how many new found in this cycle
                new_found = len(self.found_urls) - num_found_in_cycle
                if new_found > 0:
                    logger.info(f"{COLOR_GREEN}✓ Found {new_found} new agent(s) in this cycle{COLOR_RESET}")

            # Update progress based on actual requests made
            if self.requests_made_in_cycle > 0:
                new_line = cycle_start_line + self.requests_made_in_cycle
                self.current_line = new_line
            else:
                # Fallback: estimate based on rate and time
                elapsed = min(time.time() - start_time, self.run_duration)
                estimated = int(self.rate * elapsed * 0.95)
                self.current_line = cycle_start_line + estimated

            # Don't exceed total lines
            if self.current_line > self.total_lines:
                self.current_line = self.total_lines

            self.save_progress()

            # Return True only if we've processed entire wordlist
            return self.current_line >= self.total_lines

        except KeyboardInterrupt:
            logger.warning("Interrupted by user (Ctrl+C). Saving progress and results...")
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            # Parse any results in CSV before exiting
            if temp_output.exists():
                self._parse_ffuf_csv(temp_output)
                temp_output.unlink()

            # Update progress based on actual requests made
            if self.requests_made_in_cycle > 0:
                new_line = cycle_start_line + self.requests_made_in_cycle
                self.current_line = new_line

            self.save_progress()
            self.save_found_urls_to_file()
            self.cleanup()
            logger.info("Exited gracefully. Run again to resume from where you left off.")
            raise
        finally:
            # Clean up temp files
            if self.temp_wordlist.exists():
                self.temp_wordlist.unlink()
            if temp_output.exists():
                temp_output.unlink()

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_wordlist.exists():
            self.temp_wordlist.unlink()

    def _check_ffuf_installed(self) -> bool:
        """Check if ffuf is installed."""
        from shutil import which

        if which("ffuf") is None:
            logger.error("❌ ffuf is not installed!")
            logger.error("")
            logger.error("Please install ffuf:")
            logger.error("  macOS: brew install ffuf")
            logger.error("  Linux: See https://github.com/ffuf/ffuf#installation")
            logger.error("  Or run: python init_repo.py --install-external-tools")
            return False
        return True

    def run(self) -> int:
        """Main execution loop. Returns number of URLs found."""
        # Check if ffuf is installed
        if not self._check_ffuf_installed():
            return 0

        logger.info("Starting Progressive FFUF Scanner")
        logger.info(f"Target: {self.target_url}")
        logger.info(f"Wordlist: {self.wordlist_path} ({self.total_lines:,} lines)")
        logger.info(f"Starting from line: {self.current_line:,}")
        logger.info(f"Run duration: {self.run_duration}s, Pause duration: {self.pause_duration}s")
        logger.info(f"Output file: {self.output_file}")

        cycle = 1
        try:
            while self.current_line < self.total_lines:
                logger.info(f"Cycle {cycle}")

                completed = self.run_ffuf_cycle()

                if completed:
                    logger.info("ffuf completed successfully!")
                    break

                if self.current_line >= self.total_lines:
                    logger.info("Reached end of wordlist!")
                    break

                logger.info(f"Pausing for {self.pause_duration} seconds...")
                logger.info(f"Found {len(self.found_urls)} URL(s) so far...")
                time.sleep(self.pause_duration)
                cycle += 1

        finally:
            self.cleanup()

            # Save all found URLs to file
            self.save_found_urls_to_file()

            logger.info(f"{'='*60}")
            logger.info(f"Final progress: {self.current_line:,} / {self.total_lines:,} lines")
            if len(self.found_urls) > 0:
                logger.info(f"{COLOR_GREEN}Total agents found: {len(self.found_urls)}{COLOR_RESET}")
            else:
                logger.info(f"Total URLs found: {len(self.found_urls)}")
            logger.info(f"Progress saved to: {self.progress_file}")
            logger.info(f"Results saved to: {self.output_file}")
            logger.info(f"{'='*60}")

        return len(self.found_urls)


class EndpointScanner:
    """
    Wrapper class that manages scanning across multiple endpoints.
    """

    DEFAULT_ENDPOINTS = [
        # Vercel
        "https://openai-chatkit-starter-app-FUZZ.vercel.app",
        "https://openai-chatkit-FUZZ.vercel.app",
        "https://chatkit-FUZZ.vercel.app",
        "https://agentkit-FUZZ.vercel.app",
        "https://chatkit-test-FUZZ.vercel.app",
        "https://FUZZ-agentkit-chatbot.vercel.app",
        # Render
        "https://openai-chatkit-starter-app-FUZZ.onrender.com",
        "https://openai-chatkit-FUZZ.onrender.com",
        "https://chatkit-FUZZ.onrender.com",
        "https://agentkit-FUZZ.onrender.com",
        "https://chatkit-test-FUZZ.onrender.com",
        "https://FUZZ-agentkit-chatbot.onrender.com",
    ]

    def __init__(
        self,
        wordlist_path: str,
        output_file: str,
        custom_endpoint: Optional[str] = None,
        skip_defaults: bool = False,
        run_duration: int = 20,
        pause_duration: int = 15,
        rate: int = 40,
        threads: int = 10,
        filter_codes: str = "404,403",
        timeout: Optional[int] = None,
        timeout_per_endpoint: bool = False,
    ):
        self.wordlist_path = wordlist_path
        self.output_file = output_file
        self.run_duration = run_duration
        self.pause_duration = pause_duration
        self.rate = rate
        self.threads = threads
        self.filter_codes = filter_codes
        self.timeout = timeout
        self.timeout_per_endpoint = timeout_per_endpoint

        # Build endpoint list
        self.endpoints: List[str] = []
        if not skip_defaults:
            self.endpoints.extend(self.DEFAULT_ENDPOINTS)
        if custom_endpoint:
            self.endpoints.append(custom_endpoint)

        if not self.endpoints:
            raise ValueError("No endpoints to scan. Provide --endpoint or don't use --skip-defaults.")

    def get_progress_file(self, endpoint: str) -> str:
        """Generate progress filename for a specific endpoint."""
        # Create a safe filename from the endpoint URL
        safe_name = re.sub(r"[^\w\-]", "_", endpoint)
        return f"{self.wordlist_path}.{safe_name}.progress"

    def run(self) -> None:
        """Run scans across all endpoints."""
        total_endpoints = len(self.endpoints)
        total_found = 0
        scan_start_time = time.time()

        logger.info("=" * 70)
        logger.info("🚀 Agent Builder Scanner")
        logger.info("=" * 70)
        logger.info(f"Total endpoints to scan: {total_endpoints}")
        logger.info(f"Wordlist: {self.wordlist_path}")
        logger.info(f"Output file: {self.output_file}")
        if self.timeout:
            timeout_desc = "per endpoint" if self.timeout_per_endpoint else "for entire scan"
            logger.info(f"Timeout: {self.timeout}s {timeout_desc}")
        logger.info(f"Rate: {self.rate} req/s, Threads: {self.threads}")
        logger.info("=" * 70)

        try:
            for idx, endpoint in enumerate(self.endpoints, 1):
                # Check overall timeout
                if self.timeout and not self.timeout_per_endpoint:
                    elapsed = time.time() - scan_start_time
                    if elapsed >= self.timeout:
                        logger.warning(f"Overall scan timeout ({self.timeout}s) reached. Stopping.")
                        break

                logger.info(f"\n[{idx}/{total_endpoints}] Scanning: {endpoint}")

                progress_file = self.get_progress_file(endpoint)

                # Check if endpoint was already completed
                if Path(progress_file).exists():
                    scanner = ProgressiveFFUF(
                        wordlist_path=self.wordlist_path,
                        target_url=endpoint,
                        output_file=self.output_file,
                        progress_file=progress_file,
                        endpoint_name=endpoint,
                        run_duration=self.run_duration,
                        pause_duration=self.pause_duration,
                        rate=self.rate,
                        threads=self.threads,
                        filter_codes=self.filter_codes,
                    )
                    if scanner.current_line >= scanner.total_lines:
                        logger.info(f"{COLOR_GREEN}✓{COLOR_RESET} Endpoint already completed. Skipping.")
                        continue

                # Create scanner for this endpoint
                scanner = ProgressiveFFUF(
                    wordlist_path=self.wordlist_path,
                    target_url=endpoint,
                    output_file=self.output_file,
                    progress_file=progress_file,
                    endpoint_name=endpoint,
                    run_duration=self.run_duration,
                    pause_duration=self.pause_duration,
                    rate=self.rate,
                    threads=self.threads,
                    filter_codes=self.filter_codes,
                )

                # Run scan with timeout monitoring if configured
                endpoint_start = time.time()
                try:
                    if self.timeout:
                        # Run with timeout monitoring
                        while scanner.current_line < scanner.total_lines:
                            # Check per-endpoint timeout
                            if self.timeout_per_endpoint:
                                if time.time() - endpoint_start >= self.timeout:
                                    logger.warning(f"Endpoint timeout ({self.timeout}s) reached. Moving to next endpoint.")
                                    break
                            else:
                                # Check overall scan timeout
                                if time.time() - scan_start_time >= self.timeout:
                                    logger.warning(f"Overall scan timeout ({self.timeout}s) reached. Stopping.")
                                    scanner.save_found_urls_to_file()
                                    total_found += len(scanner.found_urls)
                                    # Log final summary
                                    logger.info(f"{'='*70}")
                                    logger.info(f"Scan stopped due to timeout after {idx}/{total_endpoints} endpoints")
                                    if total_found > 0:
                                        logger.info(f"{COLOR_GREEN}Total agents found: {total_found}{COLOR_RESET}")
                                    else:
                                        logger.info(f"Total URLs found: {total_found}")
                                    logger.info(f"Results saved to: {self.output_file}")
                                    logger.info(f"{'='*70}")
                                    return  # Exit the entire scan

                            scanner.run_ffuf_cycle()
                            scanner.save_found_urls_to_file()
                            if scanner.current_line >= scanner.total_lines:
                                break
                            time.sleep(scanner.pause_duration)
                        found = len(scanner.found_urls)
                    else:
                        # No timeout - run until completion
                        found = scanner.run()

                    total_found += found
                    if found > 0:
                        logger.info(f"{COLOR_GREEN}✓ Endpoint scan completed. Found {found} agent(s).{COLOR_RESET}")
                    else:
                        logger.info(f"✓ Endpoint scan completed. Found {found} URLs.")

                except KeyboardInterrupt:
                    logger.warning("User interrupted scan. Progress saved.")
                    raise

        except KeyboardInterrupt:
            logger.info("\n👋 Scan interrupted. Progress saved for all endpoints.")
            logger.info("Run again to resume from where you left off.")
            sys.exit(0)


def get_default_wordlist_path() -> str:
    """Get the path to the bundled default wordlist."""
    current_dir = Path(__file__).parent
    wordlist_path = current_dir / "wordlists" / "agent_builder_wordlist_v2.txt"
    return str(wordlist_path)
