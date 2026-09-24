"""Portable `timeout`: run a command, kill its whole process group after N seconds.

    python3 lib/timeout.py SECONDS cmd [args...]

Exits with the command's status, or 124 if the time limit was hit
(the same convention as GNU timeout). macOS ships no `timeout`.
"""
import os
import signal
import subprocess
import sys


def main():
    secs, cmd = float(sys.argv[1]), sys.argv[2:]
    p = subprocess.Popen(cmd, start_new_session=True)
    try:
        return p.wait(timeout=secs)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
        return 124


if __name__ == "__main__":
    sys.exit(main())
