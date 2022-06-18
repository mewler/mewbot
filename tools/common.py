from __future__ import annotations

import abc
from typing import Generator, List, Set

import dataclasses
import subprocess
import sys


@dataclasses.dataclass
class Annotation:
    """Schema for a GitHub action annotation, representing an error"""

    level: str
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


class ToolChain(abc.ABC):
    """Wrapper class for running linting tools, and outputting GitHub annotations"""

    folders: Set[str]
    is_ci: bool
    success: bool

    def __init__(self, *folders: str, in_ci: bool) -> None:
        self.folders = set(folders)
        self.is_ci = in_ci
        self.success = True

    def __call__(self) -> None:
        issues = list(self.run())

        if self.is_ci:
            self.github_list(issues)

        sys.exit(not self.success or len(issues) > 0)

    @abc.abstractmethod
    def run(self) -> Generator[Annotation, None, None]:
        """Abstract function for this tool chain to run its checks"""

    def run_tool(self, name: str, *args: str) -> subprocess.CompletedProcess[bytes]:
        """Helper function to run an external binary as a check"""

        arg_list = list(args)
        arg_list.extend(self.folders)

        run_result = self._run_utility(name, arg_list)

        self.success = self.success and (run_result.returncode == 0)

        return run_result

    def _run_utility(
        self, name: str, arg_list: List[str]
    ) -> subprocess.CompletedProcess[bytes]:
        run = subprocess.run(
            arg_list, stdin=subprocess.DEVNULL, capture_output=self.is_ci, check=False
        )

        if self.is_ci:
            print(f"::group::{name}")
            sys.stdout.write(run.stdout.decode("utf-8"))
            sys.stdout.write(run.stderr.decode("utf-8"))
            print("::endgroup::")
        else:
            run.stdout = b""
            run.stderr = b""

        return run

    @staticmethod
    def github_list(issues: List[Annotation]) -> None:
        """Outputs the annotations in the format for GitHub actions."""

        print("::group::Annotations")
        for issue in sorted(issues):
            print(issue)
        print("::endgroup::")

        print("Total Issues:", len(issues))
