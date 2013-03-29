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

from cupstream2distro import branchhandling


class BranchHandlingTests(BaseUnitTestCase):

    def test_branching(self):
        '''We correcly try to branch a branch'''
        source_branch = self.get_data_branch('basic', cd_in_branch=False)
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

    def test_return_log_diff_simple(self):
        '''Ensure we return the right log diff since a dedicated revision (simple branch)'''
        self.get_data_branch('simple')
        expected_content = open(os.path.join(self.data_dir, "results", "bzr_log_simple")).read()
        self.assertEquals(branchhandling._return_log_diff(3).strip(), expected_content.strip())

    def test_return_log_diff_nested(self):
        '''Ensure we return the right log diff since a dedicated revision (with nested elements)'''
        self.get_data_branch('onenested')
        expected_content = open(os.path.join(self.data_dir, "results", "bzr_log_nested")).read()
        self.assertEquals(branchhandling._return_log_diff(1).strip(), expected_content.strip())

    def test_return_log_diff_with_remerge_trunk(self):
        '''Ensure we return the right log diff but containing some remerge to trunk dating before the previous release'''
        self.get_data_branch('remergetrunk')
        expected_content = open(os.path.join(self.data_dir, "results", "bzr_log_remerge_trunk")).read()
        self.assertEquals(branchhandling._return_log_diff(12).strip(), expected_content.strip())

class BranchHandlingTestsWithErrors(BaseUnitTestCaseWithErrors):

    def test_return_exception_when_cant_branch(self):
        '''Return an exception when we can't branch'''
        source_branch = self.get_data_branch('basic')
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


class BranchHandlingTestForOfflineOnly(BaseUnitTestCase):
    '''We don't rely on system tools for those or we shouldn't use online (making merge proposal and so on)'''

    def test_get_parent_branch_from_config(self):
        '''We load and return the parent branch we should target for from config'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        self.assertEquals(branchhandling._get_parent_branch('foo'), 'lp:foo')

    def test_propose_branch_for_merging(self):
        '''We do propose a branch depending on the packaging version (and so depending on the destination)'''
        self.get_data_branch('basic')
        os.chdir('..')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), 'basic.project')
        branchhandling.propose_branch_for_merging('basic', '6.12.0daily13.02.27.in.special.ppa-0ubuntu1')

    def test_propose_branch_for_merging_with_special_chars(self):
        '''We do propose a branch depending on the packaging version (and so depending on the destination). It has special ~ and : characters not allowed by bzr'''
        self.get_data_branch('basic')
        os.chdir('..')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), 'basic.project')
        branchhandling.propose_branch_for_merging('basic', '1:6.12.0~daily13.02.27.in.special.ppa-0ubuntu1')


class BranchHandlingTestForOfflineOnlyWithErrors(BaseUnitTestCaseWithErrors):

    def test_propose_branch_for_merging_push_failed(self):
        '''We raise an exception is push failed'''
        self.get_data_branch('basic')
        os.chdir('..')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), 'basic.project')
        os.environ['MOCK_ERROR_MODE'] = "push"
        with self.assertRaises(Exception):
            branchhandling.propose_branch_for_merging('basic', '6.12.0daily13.02.27.in.special.ppa-0ubuntu1')

    def test_propose_branch_for_merging_propose_failed(self):
        '''We raise an exception is lp-propose-merge failed'''
        self.get_data_branch('basic')
        os.chdir('..')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), 'basic.project')
        os.environ['MOCK_ERROR_MODE'] = "lp-propose-merge"
        with self.assertRaises(Exception):
            branchhandling.propose_branch_for_merging('basic', '6.12.0daily13.02.27.in.special.ppa-0ubuntu1')
