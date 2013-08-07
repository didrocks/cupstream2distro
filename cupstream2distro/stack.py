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

from .settings import DEFAULT_CONFIG_STACKS_DIR, STACK_STATUS_FILENAME, STACK_STARTED_FILENAME
from .utils import ignored

_stacks_ref = {}

# TODO: should be used by a metaclass
def get_stack(release, stack_name):
    try:
        return _stacks_ref[release][stack_name]
    except KeyError:
        return Stack(release, stack_name)

class Stack():

    def __init__(self, release, stack_name):
    	self.stack_name = stack_name
    	self.release = release
        self.statusfile = os.path.join('..', '..', release, stack_name, STACK_STATUS_FILENAME)
        self.startedfile = os.path.join('..', '..', release, stack_name, STACK_STARTED_FILENAME)
        self.stack_file_path = None
        self._dependencies = None
        self._rdependencies = None
    	for stack_file_path in Stack.get_stacks_file_path(release):
            if stack_file_path.split(os.path.sep)[-1] == "{}.cfg".format(stack_name):
                self.stack_file_path = stack_file_path
                break
        if not self.stack_file_path:
            raise Exception("{}.cfg for {} doesn't exist anywhere in {}".format(stack_name, release, self.get_root_stacks_dir()))

        with open(self.stack_file_path, 'r') as f:
            cfg = yaml.load(f)
            try:
                self.forced_manualpublish = cfg['stack']['manualpublish']
            except (TypeError, KeyError):
                self.forced_manualpublish = False
        # register to the global dict
        _stacks_ref.setdefault(release, {})[stack_name] = self

    def get_status(self):
        '''Return a stack status

        0 is everything is fine and published
        1 is the stack failed in a step
        2 is the stack succeeded, but need manual publishing

        Return None if the status is not available yet'''

        cfg = yaml.load(open(self.stack_file_path))
        with ignored(KeyError):
            if cfg['stack']['status_ignored']:
                return 0
        if not os.path.isfile(self.statusfile):
            return None
        with open(self.statusfile, 'r') as f:
            return(int(f.read()))

    def is_started(self):
        '''Return True if the stack is started (dep-wait or building)'''
        if os.path.isfile(self.startedfile):
            return True
        return False

    def is_enabled(self):
        '''Return True if the stack is enabled for daily release'''
        with open(self.stack_file_path, 'r') as f:
            cfg = yaml.load(f)
            try:
                if not cfg['stack']['enabled']:
                    return False
            except KeyError:
                pass
        return True

    def get_direct_depending_stacks(self):
        '''Get a list of direct depending stacks'''
        if self._dependencies is not None:
            return self._dependencies

        with open(self.stack_file_path, 'r') as f:
            cfg = yaml.load(f)
            try:
                deps_list = cfg['stack']['dependencies']
                self._dependencies = []
                if not deps_list:
                    return self._dependencies
                for item in deps_list:
                    if isinstance(item, dict):
                        (stackname, release) = (item["name"], item["release"])
                    else:
                        (stackname, release) = (item, self.release)
                    self._dependencies.append(get_stack(release, stackname))
                logging.info("{} ({}) dependency list is: {}".format(self.stack_name, self.release, ["{} ({})".format(stack.stack_name, stack.release) for stack in self._dependencies]))
                return self._dependencies
            except (TypeError, KeyError):
                return []

    def get_direct_rdepends_stack(self):
        '''Get a list of direct rdepends'''
        if self._rdependencies is not None:
            return self._rdependencies

        self._rdependencies = []
        for stackfile in Stack.get_stacks_file_path(self.release):
            path = stackfile.split(os.path.sep)
            stack = get_stack(path[-2], path[-1].replace(".cfg", ""))
            if self in stack.get_direct_depending_stacks():
                self._rdependencies.append(stack)
        return self._rdependencies

    def generate_dep_status_message(self):
        '''Return a list of potential problems from others stack which should block current publication'''

        # TODO: get the first Stack object
        # iterate over all stacks objects from dep chain
        # call get_status on all of them

        global_dep_status_info = []
        for stack in self.get_direct_depending_stacks():
            logging.info("Check status for {} ({})".format(stack.stack_name, stack.release))
            status = stack.get_status()
            message = None
            # We should have a status for every stack
            if status is None:
                message = "Can't find status for {depstack} ({deprel}). This shouldn't happen apart if the stack is currently running. If this is the case, it means that current stack shouldn't be uploaded as the state is unknown.".format(depstack=stack, deprel=rel)
            elif status == 1:
                message = '''{depstack} ({deprel}) failed to publish. Possible cause are:
        * the stack really didn't build/can't be prepared at all.
        * the stack have integration tests not working with this previous stack.

    What's need to be done:
    Either:
        * If we want to publish both stacks: retry the integration tests for {depstack} ({deprel}), including components from this stack (check with whole ppa). If that works, both stacks should be published at the same time.
    Or:
        * If we only want to publish this stack: check that we can safely publish it by itself (e.g without the stacks it depends on). The trick there is to make sure that the stack is not relying on, or impacted by, a change that happened in one of its depends. Example: if the {depstack} ({deprel}) api changed in a way that impacts any component of the current stack, and both stacks got updated in trunk, we need to make sure we don't land only one of the two stacks which would result in a broken state. Think as well about ABI potential changes.'''.format(depstack=stack.stack_name, deprel=stack.release)
            elif status == 2:
                message = '''{depstack} ({deprel}) is in manually publish mode. Possible cause are:
        * Some part of the stack has packaging changes
        * This stack is depending on another stack not being published

    What's need to be done:
    Either:
        * If {depstack} ({deprel}) can be published, we should publish both stacks at the same time.
    Or:
        * If we only want to publish this stack: check that we can safely publish it by itself (e.g without the stacks it depends on). The trick there is to make sure that the stack is not relying on, or impacted by, a change that happened in one of its depends. Example: if the {depstack} ({deprel}) api changed in a way that impacts any component of the current stack, and both stacks got updated in trunk, we need to make sure we don't land only one of the two stacks which would result in a broken state. Think as well about ABI potential changes.'''.format(depstack=stack.stack_name, deprel=stack.release)
            elif status == 3 or status == -1:
                message = '''{depstack} ({deprel}) has been manually aborted or failed for an unknown reason. Possible cause are:
        * A job of this stack was stopped manually
        * Jenkins had an internal error/shutdown

    What's need to be done:
        * If we only want to publish this stack: check that we can safely publish it by itself (e.g without the stacks it depends on). The trick there is to make sure that the stack is not relying on, or impacted by, a change that happened in one of its depends. Example: if the {depstack} ({deprel}) api changed in a way that impacts any component of the current stack, and both stacks got updated in trunk, we need to make sure we don't land only one of the two stacks which would result in a broken state. Think as well about ABI potential changes.'''.format(depstack=stack.stack_name, deprel=stack.release)

            if message:
                logging.warning(message)
                global_dep_status_info.append(message)
        return global_dep_status_info

    @staticmethod
    def get_root_stacks_dir():
	    '''Get root stack dir'''
	    return os.environ.get('CONFIG_STACKS_DIR', DEFAULT_CONFIG_STACKS_DIR)

    @staticmethod
    def get_stacks_file_path(release):
        '''Return an iterator with all path for every discovered stack files'''
        for root, dirs, files in os.walk(os.path.join(Stack.get_root_stacks_dir(), release)):
            for candidate in files:
                if candidate.endswith('.cfg'):
                    yield os.path.join(root, candidate)

    @staticmethod
    def get_current_stack():
        '''Return current stack object based on current path (release/stackname)'''
        path = os.getcwd().split(os.path.sep)
        return get_stack(path[-2], path[-1])
