#!/usr/bin/env python3

from __future__ import annotations

import sys

import mewbot.loader

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage", sys.argv[0], " [configuration name]")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as config:
        bot = mewbot.loader.configure_bot("DemoBot", config)

    bot.run()
