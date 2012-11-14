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
BRANCH_URL = "lp:~didrocks/{}/newsnapshot"

BOT_DEBFULLNAME = "Automatic PS uploader"
BOT_DEBEMAIL = "ps-jenkins@lists.canonical.com"
BOT_KEY = "B879A3E9"

# selected arch for building arch:all packages
VIRTUALIZED_PPA_ARCH = ["i386", "amd64"]

TIME_BETWEEN_PPA_CHECKS = 15 * 60
TIME_BEFORE_STOP_LOOKING_FOR_SOURCE_PUBLISH = 30 * 60

PUBLISHER_PACKAGING_CHANGE_FILENAME = 'publisher_packaging_changes.xml'
UPLOAD_OUTSIDE_TRUNK_FILENAME_FORMAT = 'upload_out_of_trunk_{}_{}.xml'
PACKAGE_LIST_RSYNC_FILENAME_FORMAT = 'packagelist_rsync_{}'
