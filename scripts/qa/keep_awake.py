#!/usr/bin/env python3
"""Run an authorized QA command with bounded macOS idle-sleep/display assertions.
Never changes password, lock, screen-saver, energy or user-profile preferences.
Only terminates its own caffeinate child; manual lock remains available.
"""
import argparse
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds",type=int,default=43200)
    parser.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if not 1<=args.seconds<=43200:parser.error("seconds must be 1..43200")
    command=args.command[1:] if args.command[:1]==["--"] else args.command
    if not command:parser.error("Supply a QA command after --")
    awake=subprocess.Popen(["/usr/bin/caffeinate","-dimsu","-t",str(args.seconds)],start_new_session=True)
    try:
        return subprocess.run(command).returncode
    finally:
        if awake.poll() is None:
            awake.terminate()
            try:awake.wait(timeout=3)
            except subprocess.TimeoutExpired:
                awake.kill();awake.wait()


if __name__=="__main__":
    raise SystemExit(main())
