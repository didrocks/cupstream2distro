# -*- coding: UTF8 -*-
# Copyright (C) 2012 Canonical
#
# Authors:
#  Didier Roche
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

REV_STRING_FORMAT = "Automatic snapshot from revision "
PACKAGING_MERGE_COMMIT_MESSAGE = "Releasing {} to ubuntu"

BOT_DEBFULLNAME = "Automatic PS uploader"
BOT_DEBEMAIL = "didrocks@ubuntu.com"
BOT_KEY = "E4AC208E"

# selected arch for building arch:all packages
VIRTUALIZED_PPA_ARCH = ["i386", "amd64"]

TIME_BETWEEN_PPA_CHECKS = 60#15 * 60
TIME_BEFORE_STOP_LOOKING_FOR_SOURCE_PUBLISH = 120#30 * 60
