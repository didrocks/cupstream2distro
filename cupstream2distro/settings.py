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

import os

REV_STRING_FORMAT = "Automatic snapshot from revision "
NEW_CHANGELOG_PATTERN = "^{} \(.*\) (?!UNRELEASED)"
PACKAGING_MERGE_COMMIT_MESSAGE = "Releasing {} to ubuntu"
REPLACEME_TAG = "0replaceme"
BRANCH_URL = "lp:~ps-jenkins/{}/latestsnapshot"

PROJECT_CONFIG_SUFFIX = "project"

BOT_DEBFULLNAME = "Automatic PS uploader"
BOT_DEBEMAIL = "ps-jenkins@lists.canonical.com"
home_dir = os.path.expanduser("~")
CU2D_DIR = os.path.join(home_dir, "cu2d")
GNUPG_DIR = CU2D_DIR
if not os.path.isdir(GNUPG_DIR):
    GNUPG_DIR = home_dir
CRED_FILE_PATH = os.path.join(CU2D_DIR, ".cupstream_cred")
COMMON_LAUNCHPAD_CACHE_DIR = os.path.join(CU2D_DIR, "launchpad.cache")
BOT_KEY = "B879A3E9"

# selected arch for building arch:all packages
VIRTUALIZED_PPA_ARCH = ["i386", "amd64"]

TIME_BETWEEN_PPA_CHECKS = 5 * 60
TIME_BETWEEN_STACK_CHECKS = 60
TIME_BEFORE_STOP_LOOKING_FOR_SOURCE_PUBLISH = 20 * 60

PUBLISHER_ARTEFACTS_FILENAME = 'publisher.xml'
PREPARE_ARTEFACTS_FILENAME_FORMAT = 'prepare_{}_{}.xml'

OLD_STACK_DIR = 'old'
PACKAGE_LIST_RSYNC_FILENAME_PREFIX = 'packagelist_rsync'
PACKAGE_LIST_RSYNC_FILENAME_FORMAT = PACKAGE_LIST_RSYNC_FILENAME_PREFIX + '_{}'
RSYNC_PATTERN = "rsync://RSYNCSVR/cu2d_out/{}*".format(PACKAGE_LIST_RSYNC_FILENAME_PREFIX)

ROOT_CU2D = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
DEFAULT_CONFIG_STACKS_DIR = os.path.join(os.path.dirname(ROOT_CU2D), 'cupstream2distro-config', 'stacks')
STACK_STATUS_FILENAME = "stack.status"
