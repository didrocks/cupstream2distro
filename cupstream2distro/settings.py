# -*- coding: utf-8 -*-
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

REV_STRING_FORMAT = "Automatic snapshot from revision"
NEW_CHANGELOG_PATTERN = "^{} \(.*\) (?!UNRELEASED)"
PACKAGING_MERGE_COMMIT_MESSAGE = "Releasing {} (revision {} from {})"
REPLACEME_TAG = "0replaceme"
BRANCH_URL = "lp:~ps-jenkins/{}/latestsnapshot-{}"

IGNORECHANGELOG_COMMIT = "#nochangelog"

PROJECT_CONFIG_SUFFIX = "project"

BOT_DEBFULLNAME = "Ubuntu daily release"
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
# an arch we will ignore for publication if latest published version in dest doesn't build it
ARCHS_TO_EVENTUALLY_IGNORE = set(['powerpc', 'arm64', 'ppc64el'])
ARCHS_TO_UNCONDITIONALLY_IGNORE = set(['arm64', 'ppc64el'])
SRU_PPA = "ubuntu-unity/sru-staging"

TIME_BETWEEN_PPA_CHECKS = 5 * 60
TIME_BETWEEN_STACK_CHECKS = 60
TIME_BEFORE_STOP_LOOKING_FOR_SOURCE_PUBLISH = 20 * 60

PUBLISHER_ARTEFACTS_FILENAME = 'publisher.xml'
PREPARE_ARTEFACTS_FILENAME_FORMAT = 'prepare_{}.xml'

OLD_STACK_DIR = 'old'
PACKAGE_LIST_RSYNC_FILENAME_PREFIX = 'packagelist_rsync'
PACKAGE_LIST_RSYNC_FILENAME_FORMAT = PACKAGE_LIST_RSYNC_FILENAME_PREFIX + '_{}-{}'
RSYNC_PATTERN = "rsync://RSYNCSVR/cu2d_out/{}*".format(PACKAGE_LIST_RSYNC_FILENAME_PREFIX)

ROOT_CU2D = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
DEFAULT_CONFIG_STACKS_DIR = os.path.join(os.path.dirname(ROOT_CU2D), 'cupstream2distro-config', 'stacks')
STACK_STATUS_FILENAME = "stack.status"
STACK_STARTED_FILENAME = "stack.started"
STACK_BUILDING_FILENAME = "stack.building"

STACK_RUNNING_DIR = "/iSCSI/jenkins/cu2d/work"
STACK_STATUS_PUBLISHING_DIR = "/iSCSI/jenkins/cu2d/result_publishing"

# for citrain
#SILO_NAME_LIST = ("Aquaria", "Aerilon", "Canceron", "Caprica", "Gemenon", "Leonis", "Libra", "Picon",
#                  "Sagitarron", "Scorpia", "Tauron", "Virgon")
SILO_CONFIG_FILENAME = "config"
SILO_BUILDPPA_SCHEME = "didrocks/{}"
SILOS_DIR = os.path.expanduser("~/silos")
SILO_RSYNCDIR = os.path.expanduser("~/rsync")
CITRAIN_BINDIR = os.path.expanduser("~/citrain/citrain")
(SILO_EMPTY, SILO_BUILTCHECKED, SILO_PUBLISHED, SILO_DONE) = range(4)

SERIES_VERSION = {
    'precise': '12.04',
    'raring': '13.04',
    'saucy': '13.10',
    'trusty': '14.04'
}


# for testing
SILO_NAME_LIST = ("ppa", "staging", "proposed")
SILOS_DIR = os.path.expanduser("/tmp/silos")
SILO_PACKAGING_MERGE_COMMIT_MESSAGE = "Releasing {}"
BRANCH_URL = "lp:~didrocks/{}/latestsnapshot-{}"
BOT_KEY = "E4AC208E"