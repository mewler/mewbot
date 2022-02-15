#!/usr/bin/env python3

import setuptools

with open("README.md", "r", encoding="utf-8") as rmf:
    long_description = rmf.read()

with open("LICENSE.md", "r", encoding="utf-8") as lf:
    true_licence = lf.read()

setuptools.setup(
    name="mewbot",
    version="0.0.1",
    author="Benedict Harcout $ Alex Cameron",
    author_email="[Ben public email for this project] & mewbot@quicksilver.london",
    description="Light weight text based generic irc framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/javajawa/mewbot",
    project_urls={
        "Bug Tracker": "https://github.com/javajawa/mewbot/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        f"License :: OSI Approved :: {true_licence}",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",  # Might be relaxed later
)
