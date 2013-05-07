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
        self.assertEquals(branchhandling.return_log_diff(3).strip(), expected_content.strip())

    def test_return_log_diff_nested(self):
        '''Ensure we return the right log diff since a dedicated revision (with nested elements)'''
        self.get_data_branch('onenested')
        expected_content = open(os.path.join(self.data_dir, "results", "bzr_log_nested")).read()
        self.assertEquals(branchhandling.return_log_diff(1).strip(), expected_content.strip())

    def test_return_log_diff_with_remerge_trunk(self):
        '''Ensure we return the right log diff but containing some remerge to trunk dating before the previous release'''
        self.get_data_branch('remergetrunk')
        expected_content = open(os.path.join(self.data_dir, "results", "bzr_log_remerge_trunk")).read()
        self.assertEquals(branchhandling.return_log_diff(12).strip(), expected_content.strip())

    def test_extract_authors_simple(self):
        '''Extract a single line containing an author'''
        self.assertEquals(branchhandling._extract_authors("foo <foo@bar.com>"), set(["foo"]))

    def test_extract_authors_without_email(self):
        '''Extract a single line containing an author without email'''
        self.assertEquals(branchhandling._extract_authors("foo bar"), set(["foo bar"]))

    def test_extract_authors_with_multiple_simple(self):
        '''Extract a single line containing multiple authors'''
        self.assertEquals(branchhandling._extract_authors("foo bar <foo@bar.com>, baz <baz@baz.com>"), set(["foo bar", "baz"]))

    def test_extract_authors_with_multiple_missing_email_first(self):
        '''Extract a single line containing multiple authors, with first missing email'''
        self.assertEquals(branchhandling._extract_authors("foo bar, baz <baz@baz.com>"), set(["foo bar", "baz"]))

    def test_extract_authors_with_multiple_missing_email_last(self):
        '''Extract a single line containing multiple authors, with last missing email'''
        self.assertEquals(branchhandling._extract_authors("foo bar <foo@bar.com>, baz"), set(["foo bar", "baz"]))

    def test_return_bugs_one(self):
        '''Extract the bug number from a simple string'''
        self.assertEquals(branchhandling._return_bugs("https://launchpad.net/bugs/1171934"), set([1171934]))

    def test_return_bugs_double(self):
        '''Extract the bug number from a simple string containing two bugs'''
        self.assertEquals(branchhandling._return_bugs("https://launchpad.net/bugs/1171934 https://launchpad.net/bugs/1171935"), set([1171934, 1171935]))

    def test_return_bugs_multiple_lines(self):
        '''Extract the bug number from a simple string containing multiple lines'''
        self.assertEquals(branchhandling._return_bugs('''foo bar baz
            https://launchpad.net/bugs/1171934 blue bi doo
            https://launchpad.net/bugs/1171935 baz
            '''), set([1171934, 1171935]))

    def test_return_bugs_nothing(self):
        '''Extract no bug number when there is nothing'''
        self.assertEquals(branchhandling._return_bugs("bar baz doo"), set())

    def test_return_bugs_other_patterns(self):
        '''Extract bug numbers with special patterns'''
        self.assertEquals(branchhandling._return_bugs('''bug #12345, bug#12346, bug12347, bug 12348
    lp: #12349, lp:#12350, lp:12351, lp: 12352
    lp #12353, lp#12354, lp12355, lp 12356,
    Fix #12357, Fix 12358, Fix: 12359, Fix12360, Fix: #12361,
    Fixes #12362, Fixes 12363, Fixes: 12364, Fixes:12365, Fixes: #12366
    #12367 (but not 12368 for false positive)'''), set([12345 + x for x in xrange(23)]))

    def test_extract_commit_bugs(self):
        '''Extra commit and bugs from a traditional commit message merged by the upstream merger'''
        self.assertEquals(branchhandling._extract_commit_bugs('''  UnityWindow: don't draw the panel shadow above
            multiple
            lines      with extra spaces
            and more. Fixes: https://bugs.launchpad.net/bugs/1171934.
              Approved by PS Jenkins bot, Andrea Azzarone.'''), ("UnityWindow: don't draw the panel shadow above multiple lines with extra spaces and more.", set([1171934])))

    def test_extract_commit_no_bugs(self):
        '''Extra commit and bugs from a traditional commit message merged by the upstream merger without any bug'''
        self.assertEquals(branchhandling._extract_commit_bugs('''  UnityWindow: don't draw the panel shadow above
            multiple
            lines      with extra spaces
            and more.
              Approved by PS Jenkins bot, Andrea Azzarone.'''), ("UnityWindow: don't draw the panel shadow above multiple lines with extra spaces and more.", set([])))

    def test_extract_commit_manual_merge(self):
        '''Extra commit and bugs from a traditional commit message manually merged'''
        self.assertEquals(branchhandling._extract_commit_bugs('''  UnityWindow: don't draw the panel shadow above
            multiple

            lines      with extra spaces
            and more.'''), ("UnityWindow: don't draw the panel shadow above multiple lines with extra spaces and more.", set([])))

    def test_collect_author_commits_regular(self):
        '''Collect author commits and bugs for a normal bzr log'''
        with open(os.path.join(self.data_dir, 'bzrlogs', 'classiclogdiff')) as f:
            self.assertEquals(branchhandling.collect_author_commits(f.read(), set()),
                             ({'Sebastien Bacher': ["Use '%s:' string for preview hints, rather than just appending ':'. (LP: #1074038)"],
                               'Brandon Schaefer': ['EdgeBarrierController: add multiple types of subscriber results, fix edges on autohide Now when sticky keys are disabled, and the launcher is set to autohide, the mouse will hit both sides of the screen (instead of just the left side of the barrier); at that point we\'ll release the events coming from the launcher-less side of the monitor, but we\'ll use them to temporary keep the barrier "broken". (LP: #1064945)'],
                               'Marco Trevisan (Trevi\xc3\xb1o)': ['Simulating direct commit to trunk',
                                                                   'EdgeBarrierController: add multiple types of subscriber results, fix edges on autohide Now when sticky keys are disabled, and the launcher is set to autohide, the mouse will hit both sides of the screen (instead of just the left side of the barrier); at that point we\'ll release the events coming from the launcher-less side of the monitor, but we\'ll use them to temporary keep the barrier "broken". (LP: #1064945)',
                                                                   'IconRenderer: preprocess an icon if its emblem has been shown/hidden In that way we can update its transformation. (LP: #1171476, #1171663)',
                                                                   "UnityWindow: don't draw the panel shadow above a fullscreen window. (LP: #1171934)"],
                               "\xc5\x81ukasz 'sil2100' Zemczak": ['Now that we\'re using the new HUD, there have been some changes that typically cause test_hud tests to fail. Fix the tests to fit the new model. The first one is that generally we do not have indicator entries visible in the HUD anymore. Only application menu entries are in it now. The second one - the way the results are displayed is different. Now, instead of "Menu > Entry" we have "Entry (Menu)" etc.'],
                               'Andrea Azzarone': ['Disable detail view for webapp icons. (LP: #1169340)']},
                              set([1064945, 1171476, 1074038, 1169340, 1171934, 1171663])))

    def test_collect_author_commits_with_some_bugs_to_ignore(self):
        '''Collect author commits and bugs for a normal bzr log, with some bugs to ignore'''
        with open(os.path.join(self.data_dir, 'bzrlogs', 'classiclogdiff')) as f:
            self.assertEquals(branchhandling.collect_author_commits(f.read(), set([1169340, 1064945])),
                             ({'Sebastien Bacher': ["Use '%s:' string for preview hints, rather than just appending ':'. (LP: #1074038)"],
                               'Marco Trevisan (Trevi\xc3\xb1o)': ['Simulating direct commit to trunk',
                                                                   'IconRenderer: preprocess an icon if its emblem has been shown/hidden In that way we can update its transformation. (LP: #1171476, #1171663)',
                                                                   "UnityWindow: don't draw the panel shadow above a fullscreen window. (LP: #1171934)"],
                               "\xc5\x81ukasz 'sil2100' Zemczak": ['Now that we\'re using the new HUD, there have been some changes that typically cause test_hud tests to fail. Fix the tests to fit the new model. The first one is that generally we do not have indicator entries visible in the HUD anymore. Only application menu entries are in it now. The second one - the way the results are displayed is different. Now, instead of "Menu > Entry" we have "Entry (Menu)" etc.']},
                              set([1171476, 1074038, 1171934, 1171663])))


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
