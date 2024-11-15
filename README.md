# PingPy

A cross platform wrapper for the `ping` utility written in Python.

## Description

`pingpy` is a Python interface that uses `subprocess` to call the platform's `ping` utility. The `pingpy` CLI accepts a subset of `ping`'s args and unifies the interface (i.e. `-c` now always means "count" with `pingpy`), and translates the `pingpy` args to the platform's `ping` implementation.

## Usage

Run `pingpy --help` to see usage instructions.
