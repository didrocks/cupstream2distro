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
import shutil


class PackageManagerTests(BaseUnitTestCase):

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_current_version_for_series_distro(self, mocklaunchpadmanager):
        '''Get the newest version in any pocket'''

        source1 = Mock()
        source1.source_package_version = "83.09.13-0ubuntu1"
        source2 = Mock()
        source2.source_package_version = "83.09.14-0ubuntu1"
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.return_value = [source1, source2]

        return_version = packagemanager.get_current_version_for_series("foo", "rolling")

        self.assertEquals(mocklaunchpadmanager.get_ppa.call_count, 0)
        mocklaunchpadmanager.get_series.assert_called_with("rolling")
        mocklaunchpadmanager.get_ubuntu_archive.assert_called_once_with()
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.assert_called_with(status="Published", exact_match=True,
                                                                                                    source_name="foo", distro_series=mocklaunchpadmanager.get_series.return_value)
        self.assertEquals("83.09.14-0ubuntu1", return_version)

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_current_version_for_series_distro_inverse(self, mocklaunchpadmanager):
        '''Get the newest version in any pocket, inversing them'''

        source1 = Mock()
        source1.source_package_version = "83.09.13-0ubuntu1"
        source2 = Mock()
        source2.source_package_version = "83.09.14-0ubuntu1"
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.return_value = [source2, source1]

        return_version = packagemanager.get_current_version_for_series("foo", "rolling")

        self.assertEquals(mocklaunchpadmanager.get_ppa.call_count, 0)
        mocklaunchpadmanager.get_series.assert_called_with("rolling")
        mocklaunchpadmanager.get_ubuntu_archive.assert_called_once_with()
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.assert_called_with(status="Published", exact_match=True,
                                                                                                    source_name="foo", distro_series=mocklaunchpadmanager.get_series.return_value)
        self.assertEquals("83.09.14-0ubuntu1", return_version)

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_current_version_for_series_none_in_distro(self, mocklaunchpadmanager):
        '''Get the newest version, but was never published in distro'''

        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.return_value = []

        return_version = packagemanager.get_current_version_for_series("foo", "rolling")

        self.assertEquals(mocklaunchpadmanager.get_ppa.call_count, 0)
        mocklaunchpadmanager.get_series.assert_called_with("rolling")
        mocklaunchpadmanager.get_ubuntu_archive.assert_called_once_with()
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.assert_called_with(status="Published", exact_match=True,
                                                                                                    source_name="foo", distro_series=mocklaunchpadmanager.get_series.return_value)
        self.assertEquals("0", return_version)

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_current_version_for_series_ppa(self, mocklaunchpadmanager):
        '''Get the version from a ppa'''
        source_in_ppa = Mock()
        source_in_ppa.source_package_version = "83.09.13-0ubuntu1"
        mocklaunchpadmanager.get_ppa.return_value.getPublishedSources.return_value = [source_in_ppa]

        return_version = packagemanager.get_current_version_for_series("foo", "rolling", "didppa")

        self.assertEquals(mocklaunchpadmanager.get_ubuntu_archive.call_count, 0)
        mocklaunchpadmanager.get_series.assert_called_with("rolling")
        mocklaunchpadmanager.get_ppa.assert_called_once_with("didppa")
        mocklaunchpadmanager.get_ppa.return_value.getPublishedSources.assert_called_with(status="Published", exact_match=True,
                                                                                         source_name="foo", distro_series=mocklaunchpadmanager.get_series.return_value)
        self.assertEquals("83.09.13-0ubuntu1", return_version)

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_current_version_for_series_none_in_ppa(self, mocklaunchpadmanager):
        '''Get the newest version, but was never published in ppa'''

        mocklaunchpadmanager.get_ppa.return_value.getPublishedSources.return_value = []

        return_version = packagemanager.get_current_version_for_series("foo", "rolling", "didppa")

        self.assertEquals(mocklaunchpadmanager.get_ubuntu_archive.call_count, 0)
        mocklaunchpadmanager.get_series.assert_called_with("rolling")
        mocklaunchpadmanager.get_ppa.assert_called_once_with("didppa")
        mocklaunchpadmanager.get_ppa.return_value.getPublishedSources.assert_called_with(status="Published", exact_match=True,
                                                                                         source_name="foo", distro_series=mocklaunchpadmanager.get_series.return_value)
        self.assertEquals("0", return_version)

    def test_lower_version(self):
        '''Matching expectations for different cases for lower/upper version'''
        self.assertTrue(packagemanager.is_version1_higher_than_version2('2-0ubuntu1', '1-0ubuntu1'))
        self.assertTrue(packagemanager.is_version1_higher_than_version2('2-0ubuntu1', '2~daily13.10.1-0ubuntu1'))
        self.assertFalse(packagemanager.is_version1_higher_than_version2('2-0ubuntu1', '2daily13.10.1-0ubuntu1'))
        self.assertTrue(packagemanager.is_version1_higher_than_version2('2dailyrelease13.10.1.1-0ubuntu1', '2dailyrelease13.10.1-0ubuntu1'))

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

    def test_get_latest_upstream_bzr_rev_in_last_changelog(self):
        '''We always get the latest upstream bzr rev version from a changelog. Marker being in the most recent changelog'''
        self.get_data_branch('released_latestsnapshot_included')
        with open("debian/changelog") as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 10)

    def test_get_latest_upstream_bzr_rev_in_previous_changelog(self):
        '''We always get the latest upstream bzr rev version from a changelog. Marker not being in the most recent changelog'''
        self.get_data_branch('changebetween_manual_uploads')
        with open("debian/changelog") as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 3)

    def test_get_latest_upstream_bzr_rev_with_two_in_changelog(self):
        '''We always get the latest upstream bzr rev version from a changelog. We have two marker in the changelog, last on is taken'''
        self.get_data_branch('twosnapshotmarkers')
        with open("debian/changelog") as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 42)

    def test_list_packages_info_in_str(self):
        '''We return the packages info in a string'''
        package1 = Mock()
        package1.source_name = "foo"
        package1.version = "42"
        package2 = Mock()
        package2.source_name = "bar"
        package2.version = "44"
        packages_set = set([package1, package2])
        # sets are accessed randomly, so just ensure we have our strings in it.
        self.assertIn("foo (42)", packagemanager.list_packages_info_in_str(packages_set))
        self.assertIn("bar (44)", packagemanager.list_packages_info_in_str(packages_set))

    def test_get_packaging_version(self):
        '''Get latest packaging version'''
        self.get_data_branch('simple')
        self.assertEquals(packagemanager.get_packaging_version(), "42.0daily83.09.13-0ubuntu2")

    def test_list_packages_info_in_str_no_package(self):
        '''We return no packaging info if we get no package parameter'''
        self.assertEquals(packagemanager.list_packages_info_in_str(set()), "")

    @patch('cupstream2distro.packagemanager.UbuntuSourcePackage')
    @patch('cupstream2distro.packagemanager.Launchpad')
    def test_get_source_package_from_distro(self, launchpadMock, ubuntuSourcePackageMock):
        '''We grab the correct source from distro'''

        def pull_and_unpack_source():
            '''Fake pulling and unpacking from launchpad'''
            ubuntu_version_source = self.get_ubuntu_source_content_path('regular_released_branch')
            shutil.copytree(ubuntu_version_source, 'foo-42.0daily83.09.13.2')
        ubuntu_source_mock = ubuntuSourcePackageMock()
        ubuntu_source_mock.pull.side_effect = pull_and_unpack_source

        source_package_dir = packagemanager.get_source_package_from_distro("foo", "42.0daily83.09.13.2-0ubuntu1", "rolling")

        launchpadMock.login_existing.assert_called_once()
        ubuntuSourcePackageMock.assert_called_with("foo", "42.0daily83.09.13.2-0ubuntu1")
        ubuntu_source_mock.pull.assert_called_once()
        ubuntu_source_mock.unpack.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))

    @patch('cupstream2distro.packagemanager.UbuntuSourcePackage')
    @patch('cupstream2distro.packagemanager.Launchpad')
    def test_get_source_package_from_distro_with_epoc(self, launchpadMock, ubuntuSourcePackageMock):
        '''We grab the correct source from distro with epoch'''

        def pull_and_unpack_source():
            '''Fake pulling and unpacking from launchpad'''
            ubuntu_version_source = self.get_ubuntu_source_content_path('regular_released_branch')
            shutil.copytree(ubuntu_version_source, 'foo-42.0daily83.09.13.2')
        ubuntu_source_mock = ubuntuSourcePackageMock()
        ubuntu_source_mock.pull.side_effect = pull_and_unpack_source

        source_package_dir = packagemanager.get_source_package_from_distro("foo", "1:42.0daily83.09.13.2-0ubuntu1", "rolling")

        launchpadMock.login_existing.assert_called_once()
        ubuntuSourcePackageMock.assert_called_with("foo", "1:42.0daily83.09.13.2-0ubuntu1")
        ubuntu_source_mock.pull.assert_called_once()
        ubuntu_source_mock.unpack.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))
        self.assertNotIn(':', source_package_dir)

    @patch('cupstream2distro.packagemanager.UbuntuSourcePackage')
    @patch('cupstream2distro.packagemanager.Launchpad')
    def test_get_source_package_from_distro_for_native(self, launchpadMock, ubuntuSourcePackageMock):
        '''We grab the correct source from distro for native packages'''

        def pull_and_unpack_source():
            '''Fake pulling and unpacking from launchpad'''
            ubuntu_version_source = self.get_ubuntu_source_content_path('regular_released_branch')
            shutil.copytree(ubuntu_version_source, 'foo-42.0daily83.09.13.2')
        ubuntu_source_mock = ubuntuSourcePackageMock()
        ubuntu_source_mock.pull.side_effect = pull_and_unpack_source

        source_package_dir = packagemanager.get_source_package_from_distro("foo", "42.0daily83.09.13.2", "rolling")

        launchpadMock.login_existing.assert_called_once()
        ubuntuSourcePackageMock.assert_called_with("foo", "42.0daily83.09.13.2")
        ubuntu_source_mock.pull.assert_called_once()
        ubuntu_source_mock.unpack.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))

    def test_get_source_package_from_distro_not_published(self):
        '''We return none if the package was never published into the distro'''
        self.assertIsNone(packagemanager.get_source_package_from_distro("foo", "0", "rolling"))
        self.assertEqual(os.listdir('.'), [])

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

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_regular(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.12-0ubuntu1'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_epoch(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version but having an epoch'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('1:42daily83.09.12-0ubuntu1'), '1:42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_manual_upload(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version but having a previous manual upload'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.12-0ubuntu3'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_first_rerelease_sameday(self, datetimeMock):
        '''We create a new packaging version after an already first released version the same day'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.13-0ubuntu1'), '42daily83.09.13.1-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_continous_rerelease_sameday(self, datetimeMock):
        '''We create a new packaging version after an already more than one released version the same day'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.13.2-0ubuntu1'), '42daily83.09.13.3-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_manual_upload_same_day(self, datetimeMock):
        '''We create a new packaging version after an already released version the same day with some manual uploads'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.13.2-0ubuntu3'), '42daily83.09.13.3-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_without_daily(self, datetimeMock):
        '''We create a new packaging version after a normal (non daily) released version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42-0ubuntu1'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_native(self, datetimeMock):
        '''We create a new packaging version after a native released version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_sync_debian(self, datetimeMock):
        '''We create a new packaging version after a synced version from debian'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42-1'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_debian_based_manual(self, datetimeMock):
        '''We create a new packaging version after a manual based on a debian version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42-1ubuntu2'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_debian_based_daily(self, datetimeMock):
        '''We create a new packaging version after a manual based on a debian version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '83.09.13'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.12-1ubuntu2'), '42daily83.09.13-0ubuntu1')
        strftime_call.assert_called_with('%y.%m.%d')

    def test_get_packaging_sourcename(self):
        '''Get the packaging source name'''
        self.get_data_branch('onemanualupload')
        self.assertEqual("foo", packagemanager.get_packaging_sourcename())

    def test_collect_bugs_in_changelog_until_latest_snapshot_simple(self):
        '''We collect bugs in the changelog file until latest snapshot. Simple case: some bugs in an unreleased changelog'''
        source_branch = self.get_origin_branch_path("simple")
        with open(os.path.join(source_branch, 'debian', 'changelog')) as f:
            self.assertEquals(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['56789', '67890', '34567', '12345']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_extras(self):
        '''We collect bugs in the changelog file until latest snapshot. Extras syntax cases: some bugs in an unreleased changelog'''
        with open(os.path.join(self.data_dir, 'changelogs', 'different_bugs_pattern')) as f:
            self.assertEquals(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['56789', '67890', '34567', '12345',
                                                                                                             '567890', '678901', '123456', '1234567']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_no_bugs(self):
        '''We collect bugs in the changelog file until latest snapshot. No bugs, but an unreleased changelog'''
        source_branch = self.get_origin_branch_path("basic")
        with open(os.path.join(source_branch, 'debian', 'changelog')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set())

    def test_collect_bugs_in_changelog_until_latest_snapshot_no_unrelease_no_manual(self):
        '''We collect bugs in the changelog file until latest snapshot. No manual upload, no unreleased changelog'''
        with open(os.path.join(self.data_dir, 'changelogs', 'no_unrelease_no_manual')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set())

    def test_collect_bugs_in_changelog_until_latest_snapshot_multiple_unrelease(self):
        '''We collect bugs in the changelog file until latest snapshot, but no bug from it the first snapshot. Only multiple unreleased changelog content'''
        with open(os.path.join(self.data_dir, 'changelogs', 'multiple_unrelease')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['34567', '12345', '23456']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_multiple_unrelease_manual_upload(self):
        '''Test that we collect bugs in the changelog file until latest snapshot. We only collect bugs until the last manual upload'''
        with open(os.path.join(self.data_dir, 'changelogs', 'multiple_unrelease_with_release')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['23456']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_only_one_unreleased_changelog(self):
        '''Test that we collect bugs in the changelog file until latest snapshot. We collect the bugs from the one unreleased changelog'''
        with open(os.path.join(self.data_dir, 'changelogs', 'one_unreleased')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['12345']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_only_one_unreleased_changelog_no_bug(self):
        '''Test that we collect bugs in the changelog file until latest snapshot. We have no bug from the only one unreleased changelog'''
        with open(os.path.join(self.data_dir, 'changelogs', 'one_unreleased_no_bug')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set())

    def test_update_changelog_simple(self):
        '''Update a changelog from a list of one author with a known bug and bzr rev'''
        self.get_data_branch('dummypackage')
        authors = {"Foo": ["One fix for LP: #12345"]}
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "simple_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)

    def test_update_changelog_simple_no_author(self):
        '''Update a changelog from a list with no bug fix'''
        self.get_data_branch('dummypackage')
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, {})
        result_file = os.path.join(self.result_dir, "no_bug_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)

    def test_update_changelog_one_author_multiple_bugs(self):
        '''Update a changelog from a list of one author with multiple bugs'''
        self.get_data_branch('dummypackage')
        authors = {"Foo": ["One fix for LP: #12345", "Another fix for LP: #23456"]}
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "multiple_bugs_one_author_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)

    def test_update_changelog_multiple_authors(self):
        '''Update a changelog from a list of multiple authors with multiple bugs'''
        self.get_data_branch('dummypackage')
        authors = {"Foo": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "multiple_authors_bugs_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)

    def test_update_changelog_with_existing_content(self):
        '''Update a changelog when we already have existing content'''
        self.get_data_branch('basic')
        authors = {"Foo": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "existing_content_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)

    def test_update_changelog_with_existing_content_existing_author(self):
        '''Update a changelog when we already have existing content and author'''
        self.get_data_branch('basic')
        authors = {"Didier Roche": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "existing_content_author_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)

    def test_update_changelog_with_existing_content_existing_multiple_authors(self):
        '''Update a changelog when we already have existing content and multiple existing authors'''
        self.get_data_branch('basic_multiple_contents')
        authors = {"Didier Roche": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "existing_content_multiple_authors_changelog_update")
        self.assertChangelogFilesAreIdenticals("debian/changelog", result_file)


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

    def test_we_fail_if_no_boostrap_message(self):
        '''We raise an exception if no marker in the changelog'''
        self.get_data_branch('dummypackage')
        with open("debian/changelog") as f:
            with self.assertRaises(Exception):
                packagemanager.get_latest_upstream_bzr_rev(f)

    def test_raise_exception_when_upload_fail(self):
        '''We fail if the dput push failed'''
        with self.assertRaises(Exception):
            packagemanager.upload_package('foo', '1:83.09.13-0ubuntu1', 'didrocks/foo')

    @patch('cupstream2distro.packagemanager.UbuntuSourcePackage')
    @patch('cupstream2distro.packagemanager.Launchpad')
    def test_no_ubuntu_tools_installed_launchpad(self, launchpadMock, ubuntuSourcePackageMock):
        '''Test if ubuntu tools are not installed (Launchpad object)'''

        launchpadMock = None
        with self.assertRaises(Exception):
            packagemanager.get_source_package_from_distro("foo", "42.0daily83.09.13.2", "rolling")

    @patch('cupstream2distro.packagemanager.UbuntuSourcePackage')
    @patch('cupstream2distro.packagemanager.Launchpad')
    def test_no_ubuntu_tools_installed_ubuntusource(self, launchpadMock, ubuntuSourcePackageMock):
        '''Test if ubuntu tools are not installed (ubuntu source package object)'''

        ubuntuSourcePackageMock = None
        with self.assertRaises(Exception):
            packagemanager.get_source_package_from_distro("foo", "42.0daily83.09.13.2", "rolling")

    @patch('cupstream2distro.packagemanager.UbuntuSourcePackage')
    @patch('cupstream2distro.packagemanager.Launchpad')
    def test_get_source_package_from_distro_no_source(self, launchpadMock, ubuntuSourcePackageMock):
        '''Assert when we can't find the correct source in distro we try to download'''

        def pull_and_unpack_source():
            '''Fake failing pulling and unpacking from launchpad'''
            pass
        ubuntu_source_mock = ubuntuSourcePackageMock()
        ubuntu_source_mock.pull.side_effect = pull_and_unpack_source

        with self.assertRaises(Exception):
            packagemanager.get_source_package_from_distro("foo", "42.0daily83.09.13.2", "rolling")

    def test_create_new_packaging_version_with_wrong_daily_format(self):
        '''We raise an exception if there is "daily" in the previous version with a wrong format'''
        with self.assertRaises(Exception):
            packagemanager.create_new_packaging_version('42daily83.0garbage9.12-1ubuntu2')

    def test_get_packaging_sourcename_in_wrong_dir(self):
        '''Raise an excpetion when we don't find any source package name'''
        self.create_temp_workdir()
        with self.assertRaises(Exception):
            packagemanager.get_packaging_sourcename()

    def test_update_changelog_simple_lower(self):
        '''Raise an exception if we try to update a changelog from a list with a lower version'''
        self.get_data_branch('dummypackage')
        with self.assertRaises(Exception):
            packagemanager.update_changelog("1.1daily83.09.13-0ubuntu1", "rolling", 42, {})
