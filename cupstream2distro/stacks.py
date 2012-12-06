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

import logging
import os
import yaml
import subprocess
import sys

from .settings import PACKAGE_LIST_RSYNC_FILENAME_PREFIX, RSYNC_PATTERN, CONFIG_STACK_DIR, STACK_STATUS_FILENAME


def _rsync_stack_files():
    '''rsync all stack files'''
    server = os.getenv('CU2D_RSYNCSVR')
    if server:
        remoteaddr = RSYNC_PATTERN.replace('RSYNCSVR', server)
    else:
        logging.error('Please set environment variable CU2D_RSYNCSVR')
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


def get_allowed_projects():
    '''Get all projects allowed to be upload'''

    projects = []
    for file in os.listdir(CONFIG_STACK_DIR):
        if not file.endswith(".cfg"):
            continue
        with open(os.path.join(CONFIG_STACK_DIR, file), 'r') as f:
            cfg = yaml.load(f)
            if not 'stack' in cfg or not 'projects' in cfg['stack']:
                continue
            projects_list = cfg['stack']['projects']
            if not projects_list:
                continue
            # items of projects_list can be: ["proj1", "proj2"] or ["proj1": "lp:projet1/name", …]
            for project in projects_list:
                if type(project) is dict:
                    projects.append(project.keys()[0])
                else:
                    projects.append(project)
    return set(projects)


def get_depending_stacks(stackname):
    '''Get a list of depending stacks on stackname'''

    file = stackname
    if not file.endswith(".cfg"):
        file = "{}.cfg".format(file)
    with open(os.path.join(CONFIG_STACK_DIR, file), 'r') as f:
        cfg = yaml.load(f)
        if not 'stack' in cfg or not 'dependencies' in cfg['stack']:
            return []
        return cfg['stack']['dependencies']


def get_stack_status(stackname):
    '''Return a stack status

    0 is everything is fine and published
    1 is the stack failed in a step
    2 is the stack succeeded, but need manual publishing

    Return None if the status is not available yet'''

    statusfile = os.path.join('..', stackname, STACK_STATUS_FILENAME)
    if not os.path.isfile(statusfile):
        return None
    with open(statusfile, 'r') as f:
        return(int(f.read()))
