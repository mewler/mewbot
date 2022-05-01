from __future__ import annotations

from typing import List, TypedDict

import dataclasses
import subprocess
import sys


@dataclasses.dataclass
class Annotation:
    """Schema for a github action annotation, representing an error"""

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


def github_list(issues: List[Annotation]) -> None:
    print("::group::Annotations")
    for issue in sorted(issues):
        print(issue)
    print("::endgroup::")

    print("Total Issues:", len(issues))


class TypedDictRunUtility(TypedDict):
    success: bool
    completedProcess: subprocess.CompletedProcess[bytes]


def run_utility(name: str, arg_list: List[str], is_ci: bool) -> TypedDictRunUtility:
    run = subprocess.run(
        arg_list, stdin=subprocess.DEVNULL, capture_output=is_ci, check=False
    )

    if run.returncode:
        success = False
    else:
        success = True

    if is_ci:
        print(f"::group::{name}")
        sys.stdout.write(run.stdout.decode("utf-8"))
        sys.stdout.write(run.stderr.decode("utf-8"))
        print("::endgroup::")
    else:
        run.stdout = b""
        run.stderr = b""

    return {"success": success, "completedProcess": run}
