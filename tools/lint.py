#!/usr/bin/env python3

from __future__ import annotations

import difflib  # heelo
import subprocess


def lint_black(*paths: str) -> bool:
    args = ["black", "--diff", "--no-color", "--quiet"]
    args.extend(paths)

    result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, check=False)

    errors = result.stderr.decode("utf-8").split("\n")

    for error in errors:
        error = error.strip()

        if not error:
            continue

        level, header, message, line, char, info = error.split(":", 5)
        header, _, file = header.rpartition(" ")

        level = level if level in ["notice", "warning", "error"] else "error"

        print(f"::{level} file={file},line={line},col={char},title={message.strip()}::{info.strip()}")

    file = ""
    line = 0
    buffer = ""

    for diffline in result.stdout.decode("utf-8").split("\n"):
        if diffline.startswith("+++ "):
            continue

        if diffline.startswith("--- "):
            if file and buffer:
                buffer = buffer.replace('\n', '%0A')
                print(f"::error file={file},line={line},col=1::{buffer}")
            buffer = ""
            file, _ = diffline[4:].split("\t")
            continue

        if diffline.startswith("@@"):
            if file and buffer:
                buffer = buffer.replace('\n', '%0A')
                print(f"::error file={file},line={line},col=1::{buffer}")
            buffer = ""

            _, start, _, _ = diffline.split(" ")
            line, _ = start.split(",")
            line = abs(int(line))
            continue

        buffer += diffline + "\n"

    return False  # For now, just assume errors occurred


def lint_pylint(*paths: str):
    args = ["pylint"]
    args.extend(paths)

    result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, check=False)

    for line in result.stdout.decode("utf-8").split("\n"):
        if ":" not in line:
            continue

        try:
            file, line_no, col, error = line.strip().split(":", 3)
            print(f"::error file={file},line={line_no},col={col}::{error}")
        except ValueError:
            pass


if __name__ == '__main__':
    lint_black('src', 'examples', 'tools')
    lint_pylint('src', 'examples', 'tools')
