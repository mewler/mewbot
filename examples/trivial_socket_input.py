#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from os import path

import mewbot.loader

if __name__ == "__main__":
    config_dir = pathlib.Path(__file__).parent.resolve()

    with open(path.join(config_dir, "trivial_socket.yaml"), "r", encoding="utf-8") as config:
        bot = mewbot.loader.configure_bot("TrivialSocketBot", config)

    bot.run()
