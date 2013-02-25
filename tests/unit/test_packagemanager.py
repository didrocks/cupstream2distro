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

from cupstream2distro import packagemanager


class PackageManagerTests(BaseUnitTestCase):

    def test_is_new_release_needed_with_ubuntu_upload(self):
        '''We always do an ubuntu release if there has been no upload before, even if we break all criterias'''
        self.assertTrue(packagemanager.is_new_release_needed(2, 1, "foo", ubuntu_version_source=None))

    def test_release_if_at_least_one_commit(self):
        '''We release if there is at least one commit (not including latestsnapshot commit) , including an upstream change'''
        self.get_data_branch('oneupstreamchange')
        ubuntu_version_source = self.get_ubuntu_source_content_path('regular_released_branch')
        self.assertTrue(packagemanager.is_new_release_needed(12, 10, "foo", ubuntu_version_source=ubuntu_version_source))

    def test_release_if_at_least_one_commit_even_committed_before_snapshot_commit(self):
        '''We release if there is at least one commit (not including latestsnapshot commit) , including an upstream change, even if committed before the latest snapshot commit'''
        self.get_data_branch('oneupstreamchange_before_snapshot_committed')
        ubuntu_version_source = self.get_ubuntu_source_content_path('oneupstreamchange_before_snapshot_committed')
        self.assertTrue(packagemanager.is_new_release_needed(10, 8, "foo", ubuntu_version_source=ubuntu_version_source))

    def test_release_if_at_least_one_commit_and_changelog_unreleased_content(self):
        '''We release if there is at least one commit (not including latestsnapshot commit), including an upstream change, with a changelog content (UNRELEASED)'''
        self.get_data_branch('oneupstreamchange_with_unreleased_changelog_change')
        ubuntu_version_source = self.get_ubuntu_source_content_path('regular_released_branch')
        self.assertTrue(packagemanager.is_new_release_needed(12, 10, "foo", ubuntu_version_source=ubuntu_version_source))

    def test_release_if_new_content_with_manual_uploads(self):
        '''We release if there has been some manual uploads backported, but we still have at least one content difference'''
        self.get_data_branch('changebetween_manual_uploads')
        ubuntu_version_source = self.get_ubuntu_source_content_path('2manualuploads')
        self.assertTrue(packagemanager.is_new_release_needed(7, 3, "foo", ubuntu_version_source=ubuntu_version_source))

    def test_dont_release_if_only_manual_uploads(self):
        '''We don't release if we only have manual uploads, each one backported in one commit. We shouldn't need the diff as a second safety bet in this case'''
        self.get_data_branch('onlymanualuploads')
        self.assertFalse(packagemanager.is_new_release_needed(6, 3, "foo", ubuntu_version_source='something_we_shouldnt_use'))

    def test_dont_release_if_content_matches(self):
        '''We don't release if the upstream and downstream content matches, even if we had a manual upload to distro'''
        self.get_data_branch('onemanualupload')
        ubuntu_version_source = self.get_ubuntu_source_content_path('onemanualupload')
        self.assertFalse(packagemanager.is_new_release_needed(999, 1, "foo", ubuntu_version_source=ubuntu_version_source))

    def test_dont_release_if_no_commit(self):
        '''We don't release if we don't have anything new as a commit (tip == latestsnapshot)'''
        self.get_data_branch('released_latestsnapshot_included')
        self.assertFalse(packagemanager.is_new_release_needed(11, 11, "foo", ubuntu_version_source='something_we_shouldnt_use'))

    def test_dont_release_if_only_one_commit(self):
        '''We don't release if we don't have anything new as a commit (tip == latestsnapshot + 1 for the latestsnapshot commit)'''
        self.get_data_branch('released_latestsnapshot_included')
        self.assertFalse(packagemanager.is_new_release_needed(12, 11, "foo", ubuntu_version_source='something_we_shouldnt_use'))

    def test_we_fail_if_no_boostrap_message(self):
        pass


class PackageManagerTestsWithErrors(BaseUnitTestCaseWithErrors):
    pass
