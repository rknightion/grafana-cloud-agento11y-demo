#!/usr/bin/env python3
"""Bound an adapter's entire process group, including TERM-resistant descendants."""
import os
import signal
import subprocess
import sys
import time


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        if sys.platform == 'darwin' and process.poll() is not None:
            return
        raise
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            # Darwin reports EPERM for a group with no signalable members after exit.
            # Do not turn a permission failure for a still-running adapter into success.
            if sys.platform == 'darwin' and process.poll() is not None:
                return
            raise
        time.sleep(0.05)
    # Kill the group even if its original leader exited during the grace period.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def main():
    process = subprocess.Popen(sys.argv[2:], start_new_session=True)

    class Interrupted(Exception):
        def __init__(self, signum):
            self.signum = signum

    def interrupted(signum, _frame):
        raise Interrupted(signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        code = process.wait(timeout=float(sys.argv[1]))
    except Interrupted as interruption:
        code = 128 + interruption.signum
    except subprocess.TimeoutExpired:
        code = 124
    finally:
        # Never enter Popen.wait/poll from a handler that may interrupt wait's lock.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        stop_group(process)
        process.wait()
    return code if code >= 0 else 128 - code


if __name__ == '__main__':
    raise SystemExit(main())
