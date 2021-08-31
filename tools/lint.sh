#!/bin/sh

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

cd "${0%/*}/../src"

black .
flake8
mypy --strict --pretty .
pylint .
