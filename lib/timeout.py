"""Portable `timeout`: run a command, kill its whole process group after N seconds.

    python3 lib/timeout.py SECONDS cmd [args...]

Exits with the command's status, or 124 if the time limit was hit
(the same convention as GNU timeout). macOS ships no `timeout`.
The child runs in its own session, so Ctrl-C / SIGTERM / SIGHUP reaching
this wrapper are forwarded to the whole group rather than orphaning it.
"""
import os
import signal
import subprocess
import sys


def killpg(p):
    try:
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
    except ProcessLookupError:
        pass


def main():
    secs, cmd = float(sys.argv[1]), sys.argv[2:]
    p = subprocess.Popen(cmd, start_new_session=True)

    def forward(signum, _frame):
        killpg(p)
        sys.exit(128 + signum)

    for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(s, forward)
    try:
        return p.wait(timeout=secs)
    except subprocess.TimeoutExpired:
        killpg(p)
        return 124


if __name__ == "__main__":
    sys.exit(main())
