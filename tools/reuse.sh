#!/bin/sh

# SPDX-FileCopyrightText: 2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

NAME="Benedict Harcourt"
EMAIL="ben.harcourt@harcourtprogramming.co.uk"

COPYRIGHT="$NAME <$EMAIL>"

LICENSE="BSD-2-Clause"

find . \
	-path './.git' -prune -o \
	-path './.reuse' -prune -o \
	-path './LICENSES' -prune -o \
	-path './venv' -prune -o \
	-type f \
	-exec \
reuse addheader --copyright "$COPYRIGHT" --license "$LICENSE" --skip-unrecognised '{}' +
