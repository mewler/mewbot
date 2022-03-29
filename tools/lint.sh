#!/bin/sh

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

cd "${0%/*}/../src"
cd ..

MODULES="src examples"

black $MODULES
flake8 $MODULES
mypy --strict --pretty $MODULES
pylint $MODULES
