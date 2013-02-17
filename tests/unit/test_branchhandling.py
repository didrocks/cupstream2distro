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
        source_branch = self.get_data_branch('basic')
        self.get_a_temp_workdir()
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
        os.chdir(self.get_data_branch('basic'))
        self.assertFalse(branchhandling._packaging_changes_in_branch(4))

    def test_with_no_packaging_change(self):
        os.chdir(self.get_data_branch('basic'))
        self.assertFalse(branchhandling._packaging_changes_in_branch(5))


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
