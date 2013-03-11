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

from .settings import PACKAGE_LIST_RSYNC_FILENAME_PREFIX, RSYNC_PATTERN, DEFAULT_CONFIG_STACKS_DIR, STACK_STATUS_FILENAME
from .tools import get_packaging_diff_filename


def get_current_stack_infos():
    '''Return current a tuple (stackname, release) based on current path (release/stackname)'''
    path = os.getcwd().split(os.path.sep)

    return (path[-1], path[-2])


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


def get_root_stacks_dir():
    '''Get root stack dir'''
    return os.environ.get('CONFIG_STACKS_DIR', DEFAULT_CONFIG_STACKS_DIR)


def get_stacks_file_path(release):
    '''Return an iterator with all path for every discovered stack files'''
    for root, dirs, files in os.walk(os.path.join(get_root_stacks_dir(), release)):
        for candidate in files:
            if candidate.endswith('.cfg'):
                yield os.path.join(root, candidate)


def get_stack_file_path(stackname, release):
    '''Get a particular stack file based on stack infos'''
    for stack_file_path in get_stacks_file_path(release):
        if stack_file_path.split(os.path.sep)[-1] == "{}.cfg".format(stackname):
            return stack_file_path
    raise Exception("{}.cfg for {} doesn't exist anywhere in {}".format(stackname, release, get_root_stacks_dir()))


def get_allowed_projects(release):
    '''Get all projects allowed to be uploaded for this release'''

    projects = []
    for file_path in get_stacks_file_path(release):
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


def get_depending_stacks(stackname, release):
    '''Get a list of depending stacks infos (stackname, release) on stack infos

    If no release is specified, the current release is taken'''

    with open(get_stack_file_path(stackname, release), 'r') as f:
        cfg = yaml.load(f)
        try:
            deps_list = cfg['stack']['dependencies']
            return_list = []
            if not deps_list:
                return return_list
            for item in deps_list:
                if isinstance(item, dict):
                    return_list.append((item["name"], item["release"]))
                else:
                    return_list.append((item, release))
            print 'list is:', return_list
            return return_list
        except (TypeError, KeyError):
            return []


def get_stack_status(stackname, release):
    '''Return a stack status

    0 is everything is fine and published
    1 is the stack failed in a step
    2 is the stack succeeded, but need manual publishing

    Return None if the status is not available yet'''

    statusfile = os.path.join('..', '..', release, stackname, STACK_STATUS_FILENAME)
    if not os.path.isfile(statusfile):
        return None
    with open(statusfile, 'r') as f:
        return(int(f.read()))


def generate_dep_status_message(stackname, release):
    '''Return a list of potential problems from others stack which should block current publication'''

    global_dep_status_info = []
    for (stack, rel) in get_depending_stacks(stackname, release):
        logging.info("Check status for {} ({})".format(stack, rel))
        status = get_stack_status(stack, rel)
        message = None
        # We should have a status for every stack
        if status is None:
            message = "Can't find status for {depstack} ({deprel}). This shouldn't happen apart if the stack is currently running. If this is the case, it means that current stack shouldn't be uploaded as the state is unknown.".format(depstack=stack, deprel=rel)
        elif status == 1:
            message = '''{depstack} ({deprel}) failed to publish. Possible cause are:
    * the stack really didn't build/can be prepared at all.
    * the stack have integration tests not working with this previous stack.

What's need to be done:
    * The integration tests for {depstack} ({deprel}) may be rerolled with current dependant stack. If they works, both stacks should be published at the same time.
    * If we only want to publish this stack, ensure as the integration tests were maybe run from a build against {depstack}, that we can publish the current stack only safely.'''.format(depstack=stack, deprel=rel)
        elif status == 2:
            message = '''{depstack} ({deprel}) is in manually publish mode. Possible cause are:
    * Some part of the stack has packaging changes
    * This stack is depending on another stack not being published

What's need to be done:
    * The other stack can be published and we want to publish both stacks at the same time.
    * If we only want to publish this stack, ensure as the integration tests were run from a build against {depstack} ({deprel}), that we can publish the current stack only safely.'''.format(depstack=stack, deprel=rel)
        elif status == 3 or status == -1:
            message = '''{depstack} ({deprel}) has been manually aborted or failed for an unknown reason. Possible cause are:
    * A job of this stack was stopped manually
    * Jenkins had an internal error/shutdown

What's need to be done:
    * If we want to publish this stack, ensure as the integration tests were maybe run from a build against {depstack} ({deprel}), that we can publish the current stack only safely.'''.format(depstack=stack, deprel=rel)

        if message:
            logging.warning(message)
            global_dep_status_info.append(message)
    return global_dep_status_info


def get_stack_packaging_change_status(source_version_list):
    '''Return global package change status list

    source_version_list is a list of couples (source, version)'''

    packaging_change_status = []
    for (source, version) in source_version_list:
        if os.path.exists(get_packaging_diff_filename(source, version)):
            message = "Packaging change for {} ({}).".format(source, version)
            logging.warning(message)
            packaging_change_status.append(message)
    return packaging_change_status
