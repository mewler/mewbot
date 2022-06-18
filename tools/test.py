#!/usr/bin/env python3

from __future__ import annotations
from typing import List, Generator

import os
import subprocess

from tools.common import Annotation, ToolChain


class TestToolchain(ToolChain):
    def run(self) -> Generator[Annotation, None, None]:
        args = self.build_pytest_args()

        result = self.run_tool("PyTest (Testing Framework)", *args)

        yield from self.parse_pytest_out(result)

    def build_pytest_args(self) -> List[str]:
        args = ["pytest", "--cov"]

        if self.is_ci:
            # Term-only
            args.append("--cov-report=term")
            args.append("--junitxml=junit.xml")
        else:
            # Output to term
            #  term-missing gives us line numbers where things are missing
            args.append("--cov-report=term-missing")
            # Output to html
            #  .coverage_html is the folder containing the output
            args.append("--cov-report=html:.coverage_html")

        return args

    def parse_pytest_out(
        self, result: subprocess.CompletedProcess[bytes]
    ) -> Generator[Annotation, None, None]:
        outputs = result.stdout.decode("utf-8").split("\n")
        current_test = ""
        in_failures = False

        for line in outputs:
            if line == "":
                continue

            # Limit checking of some elements purely to where they are declared
            # (the "FAILURES" block)
            in_failures = self.check_if_in_failure(line, in_failures)

            if in_failures:
                if line.startswith("_") and len(line.split(" ")) == 3:
                    # New file
                    current_test = line.split(" ")[1]

                elif in_failures and ".py:" in line:
                    filepath, line, err = line.split(":", 2)
                    err = err or "OtherError"

                    yield Annotation("error", filepath, int(line), 1, err, current_test)

            if ("FAIL Required test coverage" in line) and ("not reached." in line):
                yield Annotation("error", "tools/test.py", 1, 1, "CoverageError", line)
                self.success = False

    @staticmethod
    def check_if_in_failure(line: str, in_failures: bool) -> bool:
        """Detect if we are entering or leaving the 'Failures' block"""
        if "= FAILURES =" in line:
            in_failures = True
        elif "- coverage:" in line:
            in_failures = False

        return in_failures


if __name__ == "__main__":
    is_ci = "GITHUB_ACTION" in os.environ

    testing = TestToolchain("tests", in_ci=is_ci)
    testing()
