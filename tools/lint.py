#!/usr/bin/env python3

from __future__ import annotations

from typing import Generator, Literal, Set

import dataclasses
import os
import subprocess
import sys


Level = Literal["error", "warning", "notice"]
LEVELS: Set[Level] = {"notice", "warning", "error"}


@dataclasses.dataclass
class Annotation:
    """Schema for a github action annotation, representing an error"""

    level: Level
    file: str
    line: int
    col: int
    title: str
    message: str

    def __str__(self) -> str:
        mess = self.message.replace("\n", "%0A")
        return (
            f"::{self.level} file={self.file},line={self.line},"
            f"col={self.col},title={self.title}::{mess}"
        )

    def __lt__(self, other: Annotation) -> bool:
        if not isinstance(other, Annotation):
            return False

        return self.file < other.file or self.file == other.file and self.line < other.line


class LintToolchain:
    """Wrapper class for running linting tools, and outputting GitHub annotations"""

    folders: Set[str]
    is_ci: bool
    success: bool

    def __init__(self, *folders: str, ci: bool) -> None:
        self.folders = set(folders)
        self.is_ci = ci
        self.success = True

    def __call__(self) -> Generator[Annotation, None, None]:
        yield from self.lint_black()
        yield from self.lint_flake8()
        yield from self.lint_mypy()
        yield from self.lint_pylint()

    def run_tool(self, name: str, *args: str) -> subprocess.CompletedProcess[bytes]:
        arg_list = list(args)
        arg_list.extend(self.folders)

        run = subprocess.run(
            arg_list, stdin=subprocess.DEVNULL, capture_output=self.is_ci, check=False
        )

        if run.returncode:
            self.success = False

        if self.is_ci:
            print(f"::group::{name}")
            sys.stdout.write(run.stdout.decode("utf-8"))
            sys.stdout.write(run.stderr.decode("utf-8"))
            print("::endgroup::")
        else:
            run.stdout = b""
            run.stderr = b""

        return run

    def lint_black(self) -> Generator[Annotation, None, None]:
        args = ["black"]

        if self.is_ci:
            args.extend(["--diff", "--no-color", "--quiet"])

        result = self.run_tool("Black (Formatter)", *args)

        yield from lint_black_errors(result)
        yield from lint_black_diffs(result)

    def lint_flake8(self) -> Generator[Annotation, None, None]:
        result = self.run_tool("Flake8", "flake8")

        for line in result.stdout.decode("utf-8").split("\n"):
            if ":" not in line:
                continue

            try:
                file, line_no, col, error = line.strip().split(":", 3)
                yield Annotation("error", file, int(line_no), int(col), "", error.strip())
            except ValueError:
                pass

    def lint_mypy(self) -> Generator[Annotation, None, None]:
        args = ["mypy", "--strict"]

        if not self.is_ci:
            args.append("--pretty")

        result = self.run_tool("MyPy (type checker)", *args)

        for line in result.stdout.decode("utf-8").split("\n"):
            if ":" not in line:
                continue

            try:
                file, line_no, _level, error = line.strip().split(":", 3)
                _level = _level.strip()

                if _level == "note":
                    _level = "notice"

                level: Level = _level if _level in LEVELS else "error"

                yield Annotation(level, file, int(line_no), 1, "", error.strip())
            except ValueError:
                pass

    def lint_pylint(self) -> Generator[Annotation, None, None]:
        result = self.run_tool("PyLint", "pylint")

        for line in result.stdout.decode("utf-8").split("\n"):
            if ":" not in line:
                continue

            try:
                file, line_no, col, error = line.strip().split(":", 3)
                yield Annotation("error", file, int(line_no), int(col), "", error)
            except ValueError:
                pass


def lint_black_errors(
    result: subprocess.CompletedProcess[bytes],
) -> Generator[Annotation, None, None]:
    errors = result.stderr.decode("utf-8").split("\n")
    for error in errors:
        error = error.strip()

        if not error:
            continue

        _level, header, message, line, char, info = error.split(":", 5)
        header, _, file = header.rpartition(" ")

        level: Level = _level.strip() if _level.strip() in LEVELS else "error"

        yield Annotation(level, file, int(line), int(char), message.strip(), info.strip())


def lint_black_diffs(
    result: subprocess.CompletedProcess[bytes],
) -> Generator[Annotation, None, None]:
    file = ""
    line = 0
    buffer = ""

    for diff_line in result.stdout.decode("utf-8").split("\n"):
        if diff_line.startswith("+++ "):
            continue

        if diff_line.startswith("--- "):
            if file and buffer:
                yield Annotation("error", file, line, 1, "Black alteration", buffer)

            buffer = ""
            file, _ = diff_line[4:].split("\t")
            continue

        if diff_line.startswith("@@"):
            if file and buffer:
                yield Annotation("error", file, line, 1, "Black alteration", buffer)

            _, start, _, _ = diff_line.split(" ")
            _line, _ = start.split(",")
            line = abs(int(_line))
            buffer = ""
            continue

        buffer += diff_line + "\n"


if __name__ == "__main__":
    is_ci = "GITHUB_ACTION" in os.environ

    linter = LintToolchain("src", "examples", "tools", ci=is_ci)
    issues = list(linter())

    if is_ci:
        print("::group::Annotations")
        for issue in sorted(issues):
            print(issue)
        print("::endgroup::")

        print("Total Issues:", len(issues))

    sys.exit(not linter.success or len(issues) > 0)
