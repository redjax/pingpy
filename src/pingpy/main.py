import argparse
import logging
import platform
import subprocess
import sys
from time import sleep

## Configure logging
log = logging.getLogger("pingpy")
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")
console_handler.setFormatter(formatter)
log.addHandler(console_handler)
log.setLevel("INFO")

def parse_args():
    parser = argparse.ArgumentParser(description="Ping a specified target with options for repeat count and verbosity.")
    parser.add_argument('-t', '--target', required=True, help='Target IP address or hostname to ping')
    parser.add_argument('-r', '--repeat', type=int, default=3, help='Number of times to ping. Use 0 for infinite.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')

    return parser.parse_args()


def ping_target(target, repeat, verbose):
    # Determine the ping command based on the platform
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command_base = ['ping', param, '1', target]

    log.info(f"Starting ping to {target} for {'infinite' if repeat == 0 else repeat} times")
    count_iter = 0

    try:
        while repeat == 0 or count_iter < repeat:
            try:
                result = subprocess.run(
                    command_base,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if result.returncode == 0:
                    log.info(f"Reply from {target}: {result.stdout.splitlines()[1]}")
                    if verbose:
                        log.info(f"Ping {count_iter + 1}: Success")
                else:
                    log.warning(f"No response from {target}")
                    if verbose:
                        log.warning(f"Ping {count_iter + 1}: Failure")
                        log.debug(result.stderr)

            except subprocess.SubprocessError as e:
                log.error(f"Ping failed for {target}: {e}")
            
            count_iter += 1
            if repeat != 0:
                sleep(1)  # Small delay between pings to avoid spamming

    except KeyboardInterrupt:
        log.warning("Ping operation interrupted by user")

def main():
    args = parse_args()

    # Set logging level
    if args.debug:
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")
    elif args.verbose:
        log.setLevel(logging.INFO)
        log.info("Verbose mode enabled")

    ping_target(args.target, args.repeat, args.verbose)

if __name__ == '__main__':
    main()
