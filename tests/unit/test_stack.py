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

from cupstream2distro import settings
from cupstream2distro.stack import Stack


class StackTests(BaseUnitTestCase):
    '''Module to test one stack'''

    def setUp(self):
        '''set default stack test dir'''
        super(StackTests, self).setUp()
        os.environ['CONFIG_STACKS_DIR'] = os.path.join(self.data_dir, 'stack_configs', 'default')
        self.workdir = os.path.join(self.data_dir, 'workdir', 'default')

    def test_get_current_stack_infos(self):
        '''Get stack infos based on current workdir path'''
        self.create_temp_workdir()
        path_to_create = os.path.join('head', 'stack1')
        os.makedirs(path_to_create)
        os.chdir(path_to_create)
        stack = Stack('head', 'stack1')
        self.assertEquals(Stack.get_current_stack(), stack)

    def test_get_root_stacks_dir_default(self):
        '''Default root stacks dir is the expected one'''
        os.environ.pop('CONFIG_STACKS_DIR')
        self.assertEquals(Stack.get_root_stacks_dir(), os.path.join(os.path.dirname(settings.ROOT_CU2D), 'cupstream2distro-config', 'stacks'))

    def test_tweak_stacks_dir(self):
        '''Can override the stack dir with CONFIG_STACKS_DIR'''
        self.assertEquals(Stack.get_root_stacks_dir(), os.environ['CONFIG_STACKS_DIR'])

    def test_detect_stack_files_simple(self):
        '''Detect stack files a simple directory structure filtering the none cfg ones'''
        simple_path = os.path.join(self.data_dir, 'stack_configs', 'simple')
        os.environ['CONFIG_STACKS_DIR'] = simple_path
        self.assertEquals(list(Stack.get_stacks_file_path('foo')), [os.path.join(simple_path, 'foo', 'webapp.cfg'),
                                                                    os.path.join(simple_path, 'foo', 'unity.cfg')])

    def test_detect_stack_files_regular(self):
        '''Return the expected stack files in a nested environment'''
        stack_path = os.environ['CONFIG_STACKS_DIR']
        self.assertEquals(list(Stack.get_stacks_file_path('front')), [os.path.join(stack_path, 'front', 'stack1.cfg')])
        self.assertEquals(list(Stack.get_stacks_file_path('back')), [os.path.join(stack_path, 'back', 'stack4.cfg')])
        self.assertEquals(list(Stack.get_stacks_file_path('head')), [os.path.join(stack_path, 'head', 'stack2.cfg'),
                                                                     os.path.join(stack_path, 'head', 'stack3.cfg'),
                                                                     os.path.join(stack_path, 'head', 'stack1.cfg')])

    def test_get_stack_file_path(self):
        '''Return the right file in a nested stack environment'''
        stack_path = os.environ['CONFIG_STACKS_DIR']
        self.assertEquals(Stack('back', 'stack4').stack_file_path, os.path.join(stack_path, 'back', 'stack4.cfg'))

    def test_get_stack_file_path_duplicated(self):
        '''Return the right file corresponding to the right release for duplicated filename'''
        stack_path = os.environ['CONFIG_STACKS_DIR']
        self.assertEquals(Stack('front', 'stack1').stack_file_path, os.path.join(stack_path, 'front', 'stack1.cfg'))
        self.assertEquals(Stack('head', 'stack1').stack_file_path, os.path.join(stack_path, 'head', 'stack1.cfg'))

    def test_is_started_not_started(self):
        '''Ensure a non started stack isn't seen as started'''
        shutil.copytree(self.workdir, 'workdir')
        current_workdir = os.path.join('workdir', 'head', 'stack2')
        os.chdir(current_workdir)
        self.assertFalse(Stack("head", "stack1").is_started())

    def test_is_started_not_started(self):
        '''Ensure a started stack is seen as started'''
        shutil.copytree(self.workdir, 'workdir')
        current_workdir = os.path.join('workdir', 'head', 'stack2')
        os.chdir(current_workdir)
        self.assertTrue(Stack("head", "stack3").is_started())

    def test_get_status(self):
        '''Return stack status for the current stack'''
        shutil.copytree(self.workdir, 'workdir')
        current_workdir = os.path.join('workdir', 'head', 'stack2')
        os.chdir(current_workdir)
        self.assertEquals(Stack("head", "stack1").get_status(), 0)
        self.assertEquals(Stack("head", "stack3").get_status(), 1)

    def test_ignore_status(self):
        '''Ensure that we return good status everytime we hit a "ignored" stack'''
        shutil.copytree(self.workdir, 'workdir')
        current_workdir = os.path.join('workdir', 'head', 'stack2')
        os.chdir(current_workdir)
        self.assertEquals(Stack("head", "stack2").get_status(), 0)
        self.assertEquals(Stack("back", "stack4").get_status(), 0)

    def test_get_direct_depending_stacks(self):
        '''Get stack dependencies if they exist'''
        stack = Stack('front', 'stack1')
        dep_stacks = [stack, Stack('back', 'stack4')]
        self.assertEquals(stack.get_direct_depending_stacks(), dep_stacks)

    def test_ignore_if_no_dependencies(self):
        '''Return nothing if there is no dependencies'''
        self.assertEquals(Stack('head', 'stack3').get_direct_depending_stacks(), [])

    def test_ignore_if_dependencies_empty(self):
        '''Return an empty array if there is no dependencies'''
        self.assertEquals(Stack('head', 'stack2').get_direct_depending_stacks(), [])

    def test_get_direct_depending_stacks_if_no_release(self):
        '''Get stack dependencies if there is no release specified'''
        stack = Stack('head', 'stack1')
        dep_stacks = [Stack('head', 'stack2'), Stack('front', 'stack1')]
        self.assertEquals(stack.get_direct_depending_stacks(), dep_stacks)

    def test_get_direct_rdepends_stack(self):
        '''Get a list of direct rdepends'''
        stack = Stack('head', 'stack2')
        stack_rdepends = Stack('head', 'stack1')
        self.assertEquals(stack.get_direct_rdepends_stack(), [stack_rdepends])


class StackTestsErrors(BaseUnitTestCaseWithErrors):

    def test_get_exception_for_unexisting_file(self):
        '''Return an exception if the stack file doesn't exist'''
        with self.assertRaises(Exception):
            Stack('back', 'foo')

    def test_get_exception_for_existing_file_but_wrong_release(self):
        '''Return an exception if the file doesn't exist for the current release'''
        with self.assertRaises(Exception):
            Stack('front', 'stack4')

    def test_get_exception_for_non_existing_release_path(self):
        '''Return an empty list if we give a non existing path for configuration'''
        os.environ['CONFIG_STACKS_DIR'] = "/nope"
        with self.assertRaises(Exception):
             Stack('ooo')