from __future__ import annotations

import argparse
import logging
import platform
import re
import subprocess
import sys
from time import sleep

## Configure logging
log = logging.getLogger("pingpy")
console_handler = logging.StreamHandler()


def set_logging_format(args):
    if args.debug:
        log.setLevel("DEBUG")
        formatter = logging.Formatter(
            "%(asctime)s > [%(levelname)s] > %(module)s.%(funcName)s:%(lineno)s > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    elif args.verbose:
        log.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s > [%(levelname)s] > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        log.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s > %(message)s",
            datefmt="%H:%M:%S"
        )
        
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

def parse_args():
    parser = argparse.ArgumentParser(description="Ping a specified target with options for repeat count and verbosity.")
    
    # Make the target positional (first argument after the script name)
    parser.add_argument('target', help='Target IP address or hostname to ping')

    # Optional arguments for repeat count, verbosity, and debug
    parser.add_argument('-r', '--repeat', type=int, default=3, help='Number of times to ping. Use 0 for infinite.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')

    return parser.parse_args()


def _parse_ping_response(output):
    """Parses the output of the ping command to extract the IP address, time, TTL, and success status."""
    # Pattern for Windows format (including 'time<1ms' case)
    windows_pattern = r"Reply from ([\d\.]+): bytes=\d+ time=(\d+ms|<1ms) TTL=(\d+)"
    # Pattern for Linux/macOS format
    unix_pattern = r"(\d+) bytes from ([\d\.]+): icmp_seq=\d+ ttl=(\d+) time=(\d+\.\d+) ms"
    
    # Try to match the output against the patterns
    match = re.search(windows_pattern, output)
    if match:
        ip_address = match.group(1)
        time = match.group(2)  # time can be in "ms" or "<1ms"
        ttl = match.group(3)
        success = True
    else:
        match = re.search(unix_pattern, output)
        if match:
            ip_address = match.group(2)
            time = match.group(4)
            ttl = match.group(3)
            success = True
        else:
            ip_address = None
            time = None
            ttl = None
            success = False

    return ip_address, success, time, ttl

def _ping_target(target, repeat=3, verbose=False):
    successes = 0
    failures = 0

    try:
        for i in range(repeat if repeat > 0 else sys.maxsize):
            if platform.system().lower() == 'windows':
                # Run the ping command for Windows
                result = subprocess.run(
                    ["ping", target, "-n", "1"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Run the ping command for Unix-based systems
                result = subprocess.run(
                    ["ping", "-c", "1", target],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            # Print the raw output of the ping command
            # log.debug(f"Raw ping output: {result.stdout}")

            if "TTL=" in result.stdout or "time=" in result.stdout:
                successes += 1
                log.info(f"Reply from {target} - Success")
            else:
                failures += 1
                log.warning(f"No reply from {target} - Failure")

            sleep(1)  # Optional: Add a delay between pings

    except KeyboardInterrupt:
        log.info("Ping interrupted by user (CTRL+C).")

    finally:
        log.info(f"Ping complete. Successes: {successes}, Failures: {failures}")

def ping():
    
    args = parse_args()
    set_logging_format(args)

    if args.debug:
        log.debug("Debug mode enabled")
    elif args.verbose:
        log.info("Verbose mode enabled")

    _ping_target(args.target, args.repeat, args.verbose)

if __name__ == '__main__':
    ping()
