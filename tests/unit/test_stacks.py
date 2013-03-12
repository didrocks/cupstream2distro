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

from . import BaseUnitTestCase, BaseUnitTestCaseWithErrors
import os
import shutil

from cupstream2distro import stacks, settings


class StackTests(BaseUnitTestCase):
    '''Module to test all the stack functionalities'''

    def setUp(self):
        '''set default stack test dir'''
        super(StackTests, self).setUp()
        os.environ['CONFIG_STACKS_DIR'] = os.path.join(self.data_dir, 'stack_configs', 'default')
        self.workdir = os.path.join(self.data_dir, 'workdir', 'default')

    def test_get_current_stack_infos(self):
        '''Get stack infos based on current workdir path'''
        self.create_temp_workdir()
        path_to_create = os.path.join('head', 'foo')
        os.makedirs(path_to_create)
        os.chdir(path_to_create)
        self.assertEquals(stacks.get_current_stack_infos(), ('foo', 'head'))

    def test_get_root_stacks_dir_default(self):
        '''Default root stacks dir is the expected one'''
        os.environ.pop('CONFIG_STACKS_DIR')
        self.assertEquals(stacks.get_root_stacks_dir(), os.path.join(os.path.dirname(settings.ROOT_CU2D), 'cupstream2distro-config', 'stacks'))

    def test_tweak_stacks_dir(self):
        '''Can override the stack dir with CONFIG_STACKS_DIR'''
        self.assertEquals(stacks.get_root_stacks_dir(), os.environ['CONFIG_STACKS_DIR'])

    def test_detect_stack_files_simple(self):
        '''Detect stack files a simple directory structure filtering the none cfg ones'''
        simple_path = os.path.join(self.data_dir, 'stack_configs', 'simple')
        os.environ['CONFIG_STACKS_DIR'] = simple_path
        self.assertEquals(list(stacks.get_stacks_file_path('foo')), [os.path.join(simple_path, 'foo', 'webapp.cfg'),
                                                                     os.path.join(simple_path, 'foo', 'unity.cfg')])

    def test_give_empty_list_for_empty_or_non_existing_path(self):
        '''Return an empty list if we give a non existing path for configuration'''
        os.environ['CONFIG_STACKS_DIR'] = "/nope"
        self.assertEquals(list(stacks.get_stacks_file_path('foo')), [])

    def test_detect_stack_files_regular(self):
        '''Return the expected stack files in a nested environment'''
        stack_path = os.environ['CONFIG_STACKS_DIR']
        self.assertEquals(list(stacks.get_stacks_file_path('front')), [os.path.join(stack_path, 'front', 'stack1.cfg')])
        self.assertEquals(list(stacks.get_stacks_file_path('back')), [os.path.join(stack_path, 'back', 'stack4.cfg')])
        self.assertEquals(list(stacks.get_stacks_file_path('head')), [os.path.join(stack_path, 'head', 'stack2.cfg'),
                                                                      os.path.join(stack_path, 'head', 'stack3.cfg'),
                                                                      os.path.join(stack_path, 'head', 'stack1.cfg')])

    def test_get_stack_file_path(self):
        '''Return the right file in a nested stack environment'''
        stack_path = os.environ['CONFIG_STACKS_DIR']
        self.assertEquals(stacks.get_stack_file_path('stack4', 'back'), os.path.join(stack_path, 'back', 'stack4.cfg'))

    def test_get_stack_file_path_duplicated(self):
        '''Return the right file corresponding to the right release for duplicated filename'''
        stack_path = os.environ['CONFIG_STACKS_DIR']
        self.assertEquals(stacks.get_stack_file_path('stack1', 'front'), os.path.join(stack_path, 'front', 'stack1.cfg'))
        self.assertEquals(stacks.get_stack_file_path('stack1', 'head'), os.path.join(stack_path, 'head', 'stack1.cfg'))

    def test_get_allowed_projects(self):
        '''Return a list of allowed projects to be uploaded from the stack files. Ignore invalid files and duplicates'''
        self.assertEquals(stacks.get_allowed_projects("head"), set(['toto', 'foo', 'baz', 'titi', 'tata']))

    def test_get_allowed_with_broken_stack(self):
        '''Don't break on broken stack config files (no stack key, no projects key, or no project list)'''
        os.environ['CONFIG_STACKS_DIR'] = os.path.join(self.data_dir, 'stack_configs', 'broken')
        self.assertEquals(stacks.get_allowed_projects("foo"), set())

    def test_get_depending_stacks(self):
        '''Get stack dependencies if they exist'''
        self.assertEquals(stacks.get_depending_stacks('stack1', 'front'), [('stack0', 'front'), ('stackneg', 'back')])

    def test_ignore_if_no_dependencies(self):
        '''Return nothing if there is no dependencies'''
        self.assertEquals(stacks.get_depending_stacks('stack3', 'head'), [])

    def test_ignore_if_dependencies_empty(self):
        '''Return an empty array if there is no dependencies'''
        self.assertEquals(stacks.get_depending_stacks('stack2', 'head'), [])

    def test_get_depending_stacks_if_no_release(self):
        '''Get stack dependencies if there is no release specified'''
        self.assertEquals(stacks.get_depending_stacks('stack1', 'head'), [('foo', 'head'), ('bar', 'front')])

    def test_get_stack_status(self):
        '''Return stack status from the reverse dependency stack'''
        shutil.copytree(self.workdir, 'workdir')
        current_workdir = os.path.join('workdir', 'head', 'stack2')
        os.makedirs(current_workdir)
        os.chdir(current_workdir)
        self.assertEquals(stacks.get_stack_status("stack1", "head"), 0)
        self.assertEquals(stacks.get_stack_status("stack3", "head"), 1)


class StackTestsWithOnline(BaseUnitTestCase):

    def setUp(self):
        '''set default rsync env var'''
        super(StackTestsWithOnline, self).setUp()
        os.environ['CU2D_RSYNCSVR'] = "default"

    def test_rsync_file(self):
        '''We rsync multiple files from the network'''
        stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), ['packagelist_rsync_foo-front', 'packagelist_rsync_oif-head'])

    def test_rsync_file_nothing_to_rsync(self):
        '''We get nothing through rsync'''
        os.environ['CU2D_RSYNCSVR'] = "nothing"
        # FAIL, but why?
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


class StackTestsErrors(BaseUnitTestCaseWithErrors):

    def test_get_exception_for_unexisting_file(self):
        '''Return an exception if the file doesn't exist'''
        with self.assertRaises(Exception):
            stacks.get_stack_file_path('foo', 'back')

    def test_get_exception_for_existing_file_but_wrong_release(self):
        '''Return an exception if the file doesn't exist for the current release'''
        with self.assertRaises(Exception):
            stacks.get_stack_file_path('stack4', 'front')


class StackTestsWithOnlineErrors(BaseUnitTestCaseWithErrors):

    def test_rsync_file_no_env_var(self):
        '''We error efficiently if there is no rsync environment variable'''
        os.environ['MOCK_ERROR_MODE'] = "0"
        with self.assertRaises(Exception):
            stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), [])

    def test_rsync_file_with_rsync_error(self):
        '''We raise an exception if there is an error in rsync'''
        os.environ['CU2D_RSYNCSVR'] = "default"
        with self.assertRaises(Exception):
            stacks._rsync_stack_files()
        self.assertEquals(os.listdir('.'), [])
