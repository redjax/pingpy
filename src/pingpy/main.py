import argparse
import logging
import platform
import subprocess
import sys
import re
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
    parser.add_argument('-t', '--target', required=True, help='Target IP address or hostname to ping')
    parser.add_argument('-r', '--repeat', type=int, default=3, help='Number of times to ping. Use 0 for infinite.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')

    return parser.parse_args()


def parse_ping_output(output, verbose=False):
    """
    Parse the ping output to extract IP address, success status, data sent, and round-trip time.
    """
    stats = {
        'ip_address': None,
        'success': False,
        'data_sent': None,
        'rtt': None
    }

    if platform.system().lower() == 'windows':
        # Update these regex patterns to capture bytes and RTT on Windows
        ip_match = re.search(r'Reply from ([\d.]+):', output)
        data_match = re.search(r'bytes=(\d+)', output)
        rtt_match = re.search(r'time[=<]\s*(\d+)ms', output)

        if ip_match:
            stats['ip_address'] = ip_match.group(1)
            stats['success'] = 'Request timed out' not in output
            if data_match:
                stats['data_sent'] = int(data_match.group(1))  # Capture data size
            if rtt_match:
                stats['rtt'] = int(rtt_match.group(1))  # Capture RTT in ms
    else:
        # Unix-based parsing remains the same
        ip_match = re.search(r'PING\s+.*\s+\(([\d.]+)\)', output)
        success_match = re.search(r'(\d+) bytes from ([\d.]+)', output)
        rtt_match = re.search(r'time=(\d+\.\d+) ms', output)

        if ip_match:
            stats['ip_address'] = ip_match.group(1)
        if success_match:
            stats['success'] = True
            stats['data_sent'] = int(success_match.group(1))
        if rtt_match:
            stats['rtt'] = float(rtt_match.group(1))

    if verbose:
        log.debug(f"Parsed stats: {stats}")

    return stats

def ping_target(target, repeat=3, verbose=False):
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


def main():
    args = parse_args()
    set_logging_format(args)

    if args.debug:
        log.debug("Debug mode enabled")
    elif args.verbose:
        log.info("Verbose mode enabled")

    ping_target(args.target, args.repeat, args.verbose)

if __name__ == '__main__':
    main()
