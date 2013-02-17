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

from cupstream2distro import branchhandling


class BranchHandlingTests(BaseUnitTestCase):

    def test_branching(self):
        '''We correcly try to branch a branch'''
        source_branch = self.get_data_branch('basic', cd_in_branch=False)
        print(source_branch)
        branchhandling.get_branch(source_branch, 'test_branch')
        self.assertTrue(os.path.isdir('test_branch'))
        self.assertTrue(os.path.isdir('test_branch/.bzr'))

    def test_get_tip_bzr_revision(self):
        '''We extract the tip of bzr revision'''
        os.chdir(self.get_data_branch('basic'))
        self.assertEqual(branchhandling.get_tip_bzr_revision(), 6)

    def test_detect_packaging_changes_in_branch(self):
        '''We detect packaging changes in a branch'''
        os.chdir(self.get_data_branch('basic'))
        self.assertTrue(branchhandling._packaging_changes_in_branch(3))

    def test_with_changelog_only_change(self):
        '''We detect no packaging change when a branch has the changelog changed only'''
        os.chdir(self.get_data_branch('basic'))
        self.assertFalse(branchhandling._packaging_changes_in_branch(4))

    def test_with_no_packaging_change(self):
        '''We detect no packaging change when upstream change only'''
        os.chdir(self.get_data_branch('basic'))
        self.assertFalse(branchhandling._packaging_changes_in_branch(5))

    def test_generate_diff(self):
        '''We generate the right diff'''
        self.get_data_branch('basic')
        branchhandling.generate_diff_in_branch(3, "foo", "42.0daily83.09.13-0ubuntu2")
        diff_filename = "packaging_changes_foo_42.0daily83.09.13-0ubuntu2.diff"
        source_filepath = os.path.join('..', diff_filename)
        canonical_filepath = os.path.join(self.data_dir, "results", diff_filename)
        self.assertTrue(self.are_files_identicals(source_filepath, canonical_filepath))


class BranchHandlingTestsWithErrors(BaseUnitTestCaseWithErrors):

    def test_return_exception_when_cant_branch(self):
        '''Return an exception when we can't branch'''
        source_branch = self.get_data_branch('basic')
        self.get_a_temp_workdir()
        with self.assertRaises(Exception):
            branchhandling.get_branch(source_branch, 'test_branch')

    def test_return_exception_when_cant_get_tip(self):
        '''Return an exception when we can't get the tip of a branch'''
        os.chdir(self.get_data_branch('basic'))
        with self.assertRaises(Exception):
            branchhandling.get_tip_bzr_revision()

    def test_return_exception_conditional_packaging_diff(self):
        '''Return an exception when the packaging diff presence test errored'''
        os.chdir(self.get_data_branch('basic'))
        with self.assertRaises(Exception):
            branchhandling._packaging_changes_in_branch(3)

    def test_return_exception_when_cant_generate_diff(self):
        '''Return an excpetion when we can't generate a diff'''
        os.chdir(self.get_data_branch('basic'))
        with self.assertRaises(Exception):
            branchhandling.generate_diff_in_branch(3, "foo", "42.0daily83.09.13-0ubuntu2")

