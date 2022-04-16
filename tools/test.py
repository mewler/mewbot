from __future__ import annotations

from tools.lint import Annotation

from typing import Generator

import os
import subprocess
import sys

class TestToolchain:
	
	def __init__(self, ci):
		self.is_ci = ci
		self.success = True
		
	def __call__(self) -> Generator[Annotation, None, None]:
		yield from self.run_tests()
		
	def run_tool(self, name: str, *args: str) -> subprocess.CompletedProcess[bytes]:
		arg_list = list(args)

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
	
	def run_tests(self):
		args = ["pytest"]
		args.extend(["./tests/"]) # Folder to run in
		
		# Add cov 
		#  This *MUST* have an argument after it that isn't just a file location
		args.extend(["--cov"])
		
		if is_ci:
			# Term-only
			args.extend(["--cov-report=term"])
		else:
			# Output to term
			#  term-missing gives us line numbers where things are missing
			args.extend(["--cov-report=term-missing"])
			# Output to html
			#  .coverage_html is the folder containing the output
			args.extend(["--cov-report=html:.coverage_html"])
		
		result = self.run_tool("PyTest (Testing Framework)", *args)
		
		# TODO: Something better as an output on this test
		yield

if __name__ == "__main__":
	is_ci = "GITHUB_ACTION" in os.environ
	
	testing = TestToolchain(ci = is_ci)
	issues = list(testing())

	if is_ci:
		print("::group::Annotations")
		for issue in sorted(issues):
			print(issue)
		print("::endgroup::")

		print("Total Issues:", len(issues))