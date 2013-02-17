# -*- coding: UTF8 -*-
# Copyright: (C) 2013 Canonical
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
import shutil
import unittest
import tempfile


class BaseTestCase(unittest.TestCase):
    '''Module for basetest case adding handy
    functions and keeping track of temporary direct'''

    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        cls.data_dir = os.path.join(cls.root_dir, 'data')

    @classmethod
    def addToPath(cls, path):
        '''Prepend some data to path, if path is relative, root_dir is used'''
        #TODO: check if the path is cleaned when using testnose and going to other tests types.
        if not os.path.isabs(path):
            path = os.path.join(cls.root_dir, path)
        os.environ['PATH'] = "{}:{}".format(path, os.environ["PATH"])

    def setUp(self):
        self._dirs_to_remove = []

    def tearDown(self):
        '''remove all temp dirs'''
        os.chdir(self.root_dir)
        for dir in self._dirs_to_remove:
            try:
                shutil.rmtree(dir)
            except OSError:
                pass

    def get_a_temp_workdir(self):
        '''Create a temporary work directory and cd in it'''
        tempdir = tempfile.mkdtemp()
        self._dirs_to_remove.append(tempdir)
        os.chdir(tempdir)

    def get_data_branch(self, target_branch):
        '''Return a temporary data branch directory from target_branch.

        This will perform the rename of 'bzr' dir in a .bzr one
        (can't do that in bzr itself for obvious reasons)
        The dir will be removed as part of tearDown.'''
        tempdir = tempfile.mktemp()
        self._dirs_to_remove.append(tempdir)
        shutil.copytree(os.path.join(self.data_dir, 'branches', target_branch), tempdir)
        os.rename(os.path.join(tempdir, 'bzr'), os.path.join(tempdir, '.bzr'))
        return tempdir
