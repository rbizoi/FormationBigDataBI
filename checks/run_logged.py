"""Run a check/test while teeing combined output to a timestamped reports log."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Short operation name used in the log filename")
    parser.add_argument("--log-dir", default="reports", help="Directory for operation logs")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a command after --")

    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.name).strip("-") or "check"
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    log_path = log_dir / f"{timestamp}_{safe_name}_{os.getpid()}.log"

    started = datetime.now(timezone.utc).isoformat()
    with log_path.open("w", encoding="utf-8", newline="") as log:
        log.write(f"started_at={started}\n")
        log.write(f"operation={args.name}\n")
        log.write(f"command={command!r}\n")
        log.write("--- output (stdout + stderr) ---\n")
        log.flush()
        print(f"[{args.name}] log: {log_path}", flush=True)
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log.write(line)
                log.flush()
            return_code = process.wait()
        except OSError as exc:
            message = f"could not start command: {exc}\n"
            sys.stderr.write(message)
            log.write(message)
            return_code = 127

        log.write(f"\nfinished_at={datetime.now(timezone.utc).isoformat()}\n")
        log.write(f"exit_code={return_code}\n")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
