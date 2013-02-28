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

import os
from mock import patch, Mock

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

    def test_lower_version(self):
        '''Matching expectations for different cases for lower/upper version'''
        self.assertTrue(packagemanager.is_version1_higher_than_version2('2-0ubuntu1', '1-0ubuntu1'))
        self.assertTrue(packagemanager.is_version1_higher_than_version2('2-0ubuntu1', '2~daily13.10.1-0ubuntu1'))
        self.assertFalse(packagemanager.is_version1_higher_than_version2('2-0ubuntu1', '2daily13.10.1-0ubuntu1'))
        self.assertTrue(packagemanager.is_version1_higher_than_version2('2dailyrelease13.10.1.1-0ubuntu1', '2dailyrelease13.10.1-0ubuntu1'))

    def test_get_current_version_for_series(self):
        pass

    def test_is_version_in_changelog_found(self):
        '''We find the desired version from changelog'''
        self.get_data_branch('simple')
        self.assertTrue(packagemanager.is_version_in_changelog('42.0daily83.09.13-0ubuntu1', open('debian/changelog')))

    def test_unknown_version_is_not_in_changelog(self):
        '''We don't find any unexisting version in changelog'''
        self.get_data_branch('simple')
        self.assertFalse(packagemanager.is_version_in_changelog('version_which_dont_exist', open('debian/changelog')))

    def test_unreleased_version_in_changelog(self):
        '''We return false if the version we pass is UNRELEASED in changelog'''
        self.get_data_branch('simple')
        self.assertFalse(packagemanager.is_version_in_changelog('42.0daily83.09.13-0ubuntu2', open('debian/changelog')))

    def test_never_released_version_in_changelog(self):
        '''We return true if the version we pass is 0'''
        self.get_data_branch('simple')
        self.assertTrue(packagemanager.is_version_in_changelog('0', open('debian/changelog')))

    def test_is_version_with_symbols_in_changelog_found(self):
        '''We find the desired version, containing symbols from changelog'''
        self.get_data_branch('withversionsymbols')
        self.assertTrue(packagemanager.is_version_in_changelog('42.0+bzr42daily83.09.13-0ubuntu1', open('debian/changelog')))

    def test_we_fail_if_no_boostrap_message(self):
        pass


class PackageManagerOnlineTests(BaseUnitTestCase):
    '''Test that uses online services, but as we just pull from them, we can use them'''
    
    @classmethod
    def setUpClass(cls):
        super(PackageManagerOnlineTests, cls).setUpClass()
        cls.original_settings = packagemanager.settings

    def setup_settings_mock(self, settings_mock):
        '''Setup the settings mock for the build source package method.

        Ensure that GNUPG_DIR is not a parent dir of the branch directory'''
        settings_mock.ROOT_CU2D = self.original_settings.ROOT_CU2D
        # create another temp dir not parent of the branch directory to ensure we don't mix bindmount
        # and fix magically potential code issues ;)
        settings_mock.GNUPG_DIR = self.create_temp_workdir(cd_in_dir=False)
        settings_mock.BOT_KEY = "testkey"

    @patch('cupstream2distro.packagemanager.settings')
    def test_build_source_package(self, settings_mock):
        '''Call cowbuilder and build a source package (unsigned for tests)'''
        self.setup_settings_mock(settings_mock)
        self.get_data_branch('dummypackage')
        packagemanager.build_source_package("raring", "1.1-0ubuntu1")
        os.chdir('..')
        self.assertChangesFilesAreIdenticals('foo_1.2-0ubuntu1_source.changes', os.path.join(self.data_dir, "results", 'foo_1.2-0ubuntu1_source.changes.lastcontent'))

    @patch('cupstream2distro.packagemanager.settings')
    def test_build_and_include_older_version(self, settings_mock):
        '''Call cowbuilder and build a source package (unsigned for tests), but the .changes files should contain intermediate version'''
        self.setup_settings_mock(settings_mock)
        self.get_data_branch('dummypackage')
        packagemanager.build_source_package("raring", "1.0-0ubuntu1")
        os.chdir('..')
        self.assertChangesFilesAreIdenticals('foo_1.2-0ubuntu1_source.changes', os.path.join(self.data_dir, "results", 'foo_1.2-0ubuntu1_source.changes.sincedistroversion'))

    @patch('cupstream2distro.packagemanager.settings')
    def test_build_with_other_distro_version(self, settings_mock):
        '''Call cowbuilder and build a source package (unsigned for tests) for an older distro'''
        self.setup_settings_mock(settings_mock)
        self.get_data_branch('dummypackageprecise')
        packagemanager.build_source_package("precise", "1.1-0ubuntu1")
        os.chdir('..')
        self.assertChangesFilesAreIdenticals('foo_1.2-0ubuntu1_source.changes', os.path.join(self.data_dir, "results", 'foo_1.2-0ubuntu1_source.changes.onprecise'))


class PackageManagerOnlineTestsWithErrors(BaseUnitTestCaseWithErrors):

    @classmethod
    def setUpClass(cls):
        super(PackageManagerOnlineTestsWithErrors, cls).setUpClass()
        cls.original_settings = packagemanager.settings

    def setup_settings_mock(self, settings_mock):
        '''Setup the settings mock for the build source package method.

        Ensure that GNUPG_DIR is not a parent dir of the branch directory'''
        settings_mock.ROOT_CU2D = self.original_settings.ROOT_CU2D
        # create another temp dir not parent of the branch directory to ensure we don't mix bindmount
        # and fix magically potential code issues ;)
        settings_mock.GNUPG_DIR = self.create_temp_workdir(cd_in_dir=False)
        settings_mock.BOT_KEY = "testkey"

    @patch('cupstream2distro.packagemanager.settings')
    def test_build_source_package(self, settings_mock):
        '''Fail if calling with invalid signing key'''
        self.setup_settings_mock(settings_mock)
        settings_mock.BOT_KEY = "invalidkey"
        self.get_data_branch('dummypackage')
        with self.assertRaises(Exception):
            packagemanager.build_source_package("raring", "1.1-0ubuntu1")


class PackageManagerNotforOnlineTests(BaseUnitTestCase):
    '''Test that can impact online services and we don't have control over them (dput)'''

    @classmethod
    def setUpClass(cls):
        super(PackageManagerNotforOnlineTests, cls).setUpClass()
        cls.original_settings = packagemanager.settings

    def test_upload_package(self):
        '''We upload the right package .changes files to the right ppa'''
        packagemanager.upload_package('foo', '83.09.13-0ubuntu1', 'didrocks/foo')

    def test_upload_package_with_epoch(self):
        '''We still upload the same package name than above, even if we have an epoch'''
        packagemanager.upload_package('foo', '1:83.09.13-0ubuntu1', 'didrocks/foo')


class PackageManagerTestsWithErrors(BaseUnitTestCaseWithErrors):

    def test_raise_exception_when_upload_fail(self):
        '''We fail if the dput push failed'''
        with self.assertRaises(Exception):
            packagemanager.upload_package('foo', '1:83.09.13-0ubuntu1', 'didrocks/foo')
