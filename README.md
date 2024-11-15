# PingPy

![GitHub commit activity](https://img.shields.io/github/commit-activity/y/redjax/pingpy?style=flat)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/redjax/pingpy?style=flat)
[![tests](https://github.com/redjax/pingpy/actions/workflows/tests.yml/badge.svg)](https://github.com/redjax/pingpy/actions/workflows/tests.yml)

A cross platform wrapper for the `ping` utility written in Python.

## Description

`pingpy` is a Python interface that uses `subprocess` to call the platform's `ping` utility. The `pingpy` CLI accepts a subset of `ping`'s args and unifies the interface (i.e. `-c` now always means "count" with `pingpy`), and translates the `pingpy` args to the platform's `ping` implementation.

## Usage

Run `pingpy --help` to see usage instructions.

```shell title="pingpy usage" linenums="1"
usage: pingpy [-h] [-c COUNT] [-v] [-d] [-f FILE] [-o] [-a] [-s SLEEP] target

Ping a specified target with options for repeat count, debugging & verbosity level, and optional logging to file.

positional arguments:
  target                Target IP address or hostname to ping

options:
  -h, --help            show this help message and exit
  -c COUNT, --count COUNT
                        Number of times to ping. Default: 3, 0=infinite.
  -v, --verbose         Enable verbose output
  -d, --debug           Enable debug logging
  -f FILE, --file FILE  Path to the log file
  -o, --overwrite       Overwrite the log file if it exists
  -a, --append          Append to the log file if it exists
  -s SLEEP, --sleep SLEEP
                        Number of seconds to wait between pings. Default: 1.
```
