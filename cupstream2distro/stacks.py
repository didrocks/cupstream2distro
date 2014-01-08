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

import logging
import os
import yaml
import subprocess

from .settings import PACKAGE_LIST_RSYNC_FILENAME_PREFIX, RSYNC_PATTERN
from .tools import get_packaging_diff_filename
from .stack import Stack


def _rsync_stack_files():
    '''rsync all stack files'''
    server = os.getenv('CU2D_RSYNCSVR')
    if server == "none":
        return
    elif server:
        remoteaddr = RSYNC_PATTERN.replace('RSYNCSVR', server)
    else:
        raise Exception('Please set environment variable CU2D_RSYNCSVR')

    cmd = ["rsync", '--remove-source-files', '--timeout=60', remoteaddr, '.']
    instance = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode not in (0, 23):
        raise Exception(stderr.decode("utf-8").strip())


def get_stack_files_to_sync():
    '''Return a list of tuple: (file, release)'''
    _rsync_stack_files()
    for file in os.listdir('.'):
        if file.startswith(PACKAGE_LIST_RSYNC_FILENAME_PREFIX):
            yield (file, file.split('-')[-1])


def get_allowed_projects(release):
    '''Get all projects allowed to be uploaded for this release'''

    projects = []
    for file_path in Stack.get_stacks_file_path(release):
        with open(file_path, 'r') as f:
            cfg = yaml.load(f)
            try:
                projects_list = cfg['stack']['projects']
            except (TypeError, KeyError):
                logging.warning("{} seems broken in not having stack or projects keys".format(file_path))
                continue
            if not projects_list:
                logging.warning("{} don't have any project list".format(file_path))
                continue
            for project in projects_list:
                if isinstance(project, dict):
                    projects.append(project.keys()[0])
                else:
                    projects.append(project)
    return set(projects)

def get_stack_packaging_change_status(source_version_list):
    '''Return global package change status list

    # FIXME: added too many infos now, should only be: (source, version)
    source_version_list is a list of couples (source, version, tip_rev, target_branch)'''

    packaging_change_status = []
    for (source, version, tip_rev, target_branch) in source_version_list:
        if os.path.exists(get_packaging_diff_filename(source, version)):
            message = "Packaging change for {} ({}).".format(source, version)
            logging.warning(message)
            packaging_change_status.append(message)
    return packaging_change_status
