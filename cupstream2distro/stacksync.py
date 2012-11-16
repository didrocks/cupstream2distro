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
import subprocess
import sys

from .settings import PACKAGE_LIST_RSYNC_FILENAME_PREFIX, RSYNC_PATTERN


def _rsync_stack_files():
    '''rsync all stack files'''
    server = os.getenv('CU2D_RSYNCSVR')
    if server:
        remoteaddr = RSYNC_PATTERN.replace('RSYNCSVR', server)
    else:
        print('ERROR: Please set environment variable CU2D_RSYNCSVR')
        sys.exit(1)

    cmd = ["rsync", '--remove-source-files', remoteaddr, '.']
    instance = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode not in (0, 23):
        raise Exception(stderr.decode("utf-8").strip())


def get_stack_files_to_sync():
    '''Return a list of file'''
    _rsync_stack_files()
    for file in os.listdir('.'):
        if file.startswith(PACKAGE_LIST_RSYNC_FILENAME_PREFIX):
            yield file
