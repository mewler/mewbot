from __future__ import annotations
from typing import List, Generator

import subprocess
import sys
import os

from tools.common import Annotation, github_list, run_utility


class TestToolchain:
    is_ci: bool
    success: bool

    def __init__(self, in_ci: bool) -> None:
        self.is_ci = in_ci
        self.success = True

    def __call__(self) -> Generator[Annotation, None, None]:
        yield from self.run_tests()

    def run_tool(self, name: str, *args: str) -> subprocess.CompletedProcess[bytes]:
        arg_list = list(args)

        run_result = run_utility(name, arg_list, self.is_ci)

        self.success = run_result["success"]

        return run_result["completedProcess"]

    def run_tests(self) -> Generator[Annotation, None, None]:
        args = self.build_pytest_args()

        result = self.run_tool("PyTest (Testing Framework)", *args)

        yield from self.parse_pytest_out(result)

    def build_pytest_args(self) -> List[str]:
        args = ["pytest"]
        args.extend(["./tests/"])  # Folder to run in

        # Add cov
        #  This *MUST* have an argument after it that isn't just a file location
        args.extend(["--cov"])

        if self.is_ci:
            # Term-only
            args.extend(["--cov-report=term"])
        else:
            # Output to term
            #  term-missing gives us line numbers where things are missing
            args.extend(["--cov-report=term-missing"])
            # Output to html
            #  .coverage_html is the folder containing the output
            args.extend(["--cov-report=html:.coverage_html"])

        return args

    def parse_pytest_out(
        self,
        result: subprocess.CompletedProcess[bytes],
    ) -> Generator[Annotation, None, None]:
        # flake8: noqa: max-complexity: 10
        # 10 is the current raised complexity floor of this method. The complexity is due to
        # various different text options for the line; which is exacerbated by a toggling state
        # on if the parser is in the "FAILURES" block or otherwise.

        outputs = result.stdout.decode("utf-8").split("\n")
        current_test = ""
        in_failures = False

        for output in outputs:
            if output == "":
                continue

            # Limit checking of some elements purely to where they are declared (the "FAILURES"
            # block)
            if "= FAILURES =" in output:
                in_failures = True
            elif "- coverage:" in output:
                in_failures = False

            if in_failures:
                if output.startswith("_") and len(output.split(" ")) == 3:
                    # New file
                    current_test = output.split(" ")[1]

                elif in_failures and ".py:" in output:
                    split_output = output.split(":")
                    this_filepath = split_output[0]
                    this_line = int(split_output[1])
                    this_err = split_output[2].strip()
                    if this_err == "":
                        this_err = "OtherError"
                    yield Annotation(
                        "error", this_filepath, this_line, 1, this_err, current_test
                    )

            if ("FAIL Required test coverage" in output) and ("not reached." in output):
                yield Annotation("error", "tools/test.py", 1, 1, "CoverageError", output)
                self.success = False


if __name__ == "__main__":
    is_ci = "GITHUB_ACTION" in os.environ

    testing = TestToolchain(in_ci=is_ci)
    issues = list(testing())

    if is_ci:
        github_list(issues)

    sys.exit(not testing.success or len(issues) > 0)
