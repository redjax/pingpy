from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import logging
from pathlib import Path
import platform
import re
import subprocess
import sys
from time import sleep

## Initialize logging
log = logging.getLogger("pingpy")
console_handler = logging.StreamHandler()

@dataclass
class PingArgs:
    """Dataclass for CLI args.
    
    Params:
        target (str): Target IP address or hostname to ping.
        count (int): Number of times to ping the target. Default is 1.
        verbose (bool): Whether to print verbose output. Default is False.
        debug (bool): Whether to enable debug logging. Default is False.
        file (str): Path to the log file. Default is None.
        overwrite (bool): Whether to overwrite the log file if it exists. Default is False.
        append (bool): Whether to append to the log file if it exists. Default is False.
        sleep (int): Number of seconds to wait between pings. Default is 1.
    """

    target: str = field(default=None)
    count: int = field(default=1)
    verbose: bool = field(default=False)
    debug: bool = field(default=False)
    file: str | None = field(default=None)
    overwrite: bool = field(default=False)
    append: bool = field(default=False)
    sleep: int = field(default=1)


def set_logging_format(args):
    """Setup logging based on args passed to CLI."""
    formatter = None
    
    ## -d/--debug arg
    if args.debug:
        log.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s > [%(levelname)s] > %(module)s.%(funcName)s:%(lineno)s > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    ## -v/--verbose arg
    elif args.verbose:
        log.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s > [%(levelname)s] > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    ## Standard logging
    else:
        log.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s > %(message)s",
            datefmt="%H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    ## Set up file logging if a file path is provided
    if args.file:
        file_path = Path(args.file)
        
        if file_path.exists() and not (args.append or args.overwrite):
            log.error(f"File {file_path} already exists. Use -a/--append or -o/--overwrite to modify.")
            sys.exit(1)

        ## Create directories if they do not exist
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            msg = f"({type(exc)}) Unable to create directory: '{file_path.parent}'. Details: {exc}"
            log.error(msg)
            sys.exit(1)

        ## File mode based on append/overwrite
        file_mode = 'a' if args.append else 'w'
        file_handler = logging.FileHandler(file_path, mode=file_mode)
        file_formatter = logging.Formatter(
            "%(asctime)s | [%(levelname)s] | %(message)s",
            datefmt="%H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel("INFO")
        
        log.addHandler(file_handler)

def parse_args():
    """Parse CLI args with argparse.
    
    Returns:
        (argparse.Namespace): Parsed arguments namespace.

    """
    parser = argparse.ArgumentParser("pingpy", description="Ping a specified target with options for repeat count, debugging & verbosity level, and optional logging to file.")
    
    ## Make the target positional (first argument after the script name)
    parser.add_argument('target', help='Target IP address or hostname to ping')

    ## Optional arguments for repeat count, verbosity, and debug
    parser.add_argument('-c', '--count', type=int, default=3, help='Number of times to ping. Default: 3, 0=infinite.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-f', '--file', type=str, help='Path to the log file')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite the log file if it exists')
    parser.add_argument('-a', '--append', action='store_true', help='Append to the log file if it exists')
    parser.add_argument('-s', '--sleep', type=int, default=1, help='Number of seconds to wait between pings. Default: 1.')

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

def _ping_target(target, repeat=3, sleep_seconds=1,verbose=False):
    """Pings a target IP address or hostname a specified number of times and logs the results.
    
    Params:
        target (str): Target IP address or hostname to ping.
        repeat (int): Number of times to ping the target. Default is 3.
        sleep_seconds (int): Number of seconds to wait between pings. Default is 1 second.
        verbose (bool): Whether to print verbose output. Default is False.
    """
    ## Initialize counts
    successes = 0
    failures = 0
    
    log.info(f"Pinging {target} [repeat: {'indefinitely' if repeat == 0 else str(repeat) +  ' time(s)'}]")

    try:
        for i in range(repeat if repeat > 0 else sys.maxsize):
            log.debug(f"Ping [{i + 1}/{repeat}]")

            if platform.system().lower() == 'windows':
                ## Run the ping command for Windows
                try:
                    result = subprocess.run(
                        ["ping", target, "-n", "1"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                except subprocess.CalledProcessError as e:
                    log.error(f"Error running ping command: {e}")
                    sys.exit(1)

            else:
                ## Run the ping command for Unix-based systems
                try:
                    result = subprocess.run(
                        ["ping", "-c", "1", target],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                except subprocess.CalledProcessError as e:
                    log.error(f"Error running ping command: {e}")
                    sys.exit(1)

            if "TTL=" in result.stdout or "time=" in result.stdout:
                ## Ping success
                successes += 1
                log.info(f"Reply from {target} - Success")
            else:
                ## Ping failure
                failures += 1
                log.warning(f"No reply from {target} - Failure")

            ## Optional: Add a delay between pings
            sleep(sleep_seconds)

    except KeyboardInterrupt:
        log.info("Ping interrupted by user (CTRL+C).")

    finally:
        log.info(f"Ping {target} complete. Successes: {successes}, Failures: {failures}")

def ping():
    """Pingpy entrypoint.
    
    Description:
        Parses command-line arguments, sets up logging, and calls the ping function.
    """
    ## Parse CLI arguments    
    args = parse_args()
    ## Initialize pingpy logging
    set_logging_format(args)
    
    ## Initialize PingArgs class
    ping_settings: PingArgs = PingArgs(**vars(args))
    log.debug(f"Ping settings: {ping_settings}")
    
    if ping_settings.debug:
        log.debug("Debug mode enabled")
    elif ping_settings.verbose:
        log.debug("Verbose mode enabled")

    ## Start ping
    try:
        _ping_target(ping_settings.target, ping_settings.count, ping_settings.sleep, ping_settings.verbose)
    except Exception as exc:
        msg = f"An error occurred while pinging {ping_settings.target}. Details: {exc}"
        log.error(msg)
        sys.exit(1)

if __name__ == '__main__':
    ping()
