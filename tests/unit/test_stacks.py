# -*- coding: utf-8 -*-
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

from . import BaseUnitTestCase, BaseUnitTestCaseWithErrors
import os
import shutil

from cupstream2distro import stacks, settings


class StackTests(BaseUnitTestCase):
    '''Module to test all the stacks functionalities'''

    def setUp(self):
        '''set default stack test dir'''
        super(StackTests, self).setUp()
        os.environ['CONFIG_STACKS_DIR'] = os.path.join(self.data_dir, 'stack_configs', 'default')
        self.workdir = os.path.join(self.data_dir, 'workdir', 'default')


    def test_get_allowed_projects(self):
        '''Return a list of allowed projects to be uploaded from the stack files. Ignore invalid files and duplicates'''
        self.assertEquals(stacks.get_allowed_projects("head"), set(['toto', 'foo', 'baz', 'titi', 'tata']))

    def test_get_allowed_with_broken_stack(self):
        '''Don't break on broken stack config files (no stack key, no projects key, or no project list)'''
        os.environ['CONFIG_STACKS_DIR'] = os.path.join(self.data_dir, 'stack_configs', 'broken')
        self.assertEquals(stacks.get_allowed_projects("foo"), set())


class StackTestsWithOnline(BaseUnitTestCase):

    def setUp(self):
        '''set default rsync env var'''
        super(StackTestsWithOnline, self).setUp()
        os.environ['CU2D_RSYNCSVR'] = "default"

    @classmethod
    def tearDownClass(cls):
        super(StackTestsWithOnline, cls).setUpClass()
        os.environ.pop('CU2D_RSYNCSVR')

    def test_rsync_file(self):
        '''We rsync multiple files from the network'''
        stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), ['packagelist_rsync_foo-front', 'packagelist_rsync_oif-head'])

    def test_rsync_file_nothing_to_rsync(self):
        '''We get nothing through rsync'''
        os.environ['CU2D_RSYNCSVR'] = "nothing"
        stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), [])

    def test_get_stack_files_to_sync(self):
        '''We get the default tuple for stack files to sync'''
        self.assertEquals(list(stacks.get_stack_files_to_sync()), [('packagelist_rsync_foo-front', 'front'),
                                                                   ('packagelist_rsync_oif-head', 'head')])

    def test_get_stack_files_to_sync_nothing_to_sync(self):
        '''Empty result if nothing to sync'''
        os.environ['CU2D_RSYNCSVR'] = "nothing"
        stacks._rsync_stack_files()
        self.assertEquals(list(stacks.get_stack_files_to_sync()), [])


class StackTestsWithOnlineErrors(BaseUnitTestCaseWithErrors):

    def setUp(self):
        '''set default rsync env var'''
        super(StackTestsWithOnlineErrors, self).setUp()
        os.environ['CU2D_RSYNCSVR'] = "default"

    @classmethod
    def tearDownClass(cls):
        super(StackTestsWithOnlineErrors, cls).setUpClass()
        os.environ.pop('CU2D_RSYNCSVR')

    def test_rsync_file_no_env_var(self):
        '''We error efficiently if there is no rsync environment variable'''
        os.environ['MOCK_ERROR_MODE'] = "0"
        os.environ.pop('CU2D_RSYNCSVR')
        with self.assertRaises(Exception):
            stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), [])

    def test_rsync_file_with_rsync_error(self):
        '''We raise an exception if there is an error in rsync'''
        with self.assertRaises(Exception):
            stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), [])
