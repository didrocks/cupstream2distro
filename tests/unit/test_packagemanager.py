# -*- coding: utf-8 -*-
# Copyright: (C) 2013-2014 Canonical
#
# Authors:
#  Didier Roche
#  Rodney Dawes
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
import subprocess
import urllib


class PackageManagerTests(BaseUnitTestCase):

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_current_version_for_series_distro(self, mocklaunchpadmanager):
        '''Get the newest version in any pocket'''

        source1 = Mock()
        source1.source_package_version = "83.09.14-0ubuntu1"
        source2 = Mock()
        source2.source_package_version = "83.09.13-0ubuntu1"
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.return_value = [source1, source2]

        return_version = packagemanager.get_current_version_for_series("foo", "rolling")

        self.assertEquals(mocklaunchpadmanager.get_ppa.call_count, 0)
        mocklaunchpadmanager.get_series.assert_called_with("rolling")
        mocklaunchpadmanager.get_ubuntu_archive.assert_called_once_with()
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.assert_called_with(exact_match=True,
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
        mocklaunchpadmanager.get_ubuntu_archive.return_value.getPublishedSources.assert_called_with(exact_match=True,
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
        mocklaunchpadmanager.get_ppa.return_value.getPublishedSources.assert_called_with(exact_match=True,
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
        mocklaunchpadmanager.get_ppa.return_value.getPublishedSources.assert_called_with(exact_match=True,
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

    def test_get_latest_upstream_bzr_rev_with_only_bootstrap(self):
        '''We always get the latest upstream bzr rev version from a changelog. We only have the bootstrap version.'''
        with open(os.path.join(self.changelogs_file_dir, 'distro_with_only_bootstrap')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 42)

    def test_get_latest_upstream_bzr_rev_in_previous_changelog(self):
        '''We always get the latest upstream bzr rev version from a changelog. Marker not being in the most recent changelog'''
        self.get_data_branch('changebetween_manual_uploads')
        with open("debian/changelog") as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 3)

    def test_get_latest_upstream_bzr_rev_with_two_in_changelog(self):
        '''We always get the latest upstream bzr rev version from a changelog. We have two marker in the changelog, last one is taken'''
        self.get_data_branch('twosnapshotmarkers')
        with open("debian/changelog") as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 42)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_without_distro(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa without a distro version'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_without_distro')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/next'), 8)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_and_distro(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa and a distro version'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_with_distro')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/next'), 42)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_and_distro_first(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa and a distro version appearing first in the result'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_with_distro_first')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/next'), 8)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_and_distro_without_dest_ppa_rev(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa and a distro version without dest_ppa rev'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_with_distro_without_dest_ppa')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/next'), 42)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_with_2_versions(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa with 2 marker version in the same changelog'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_with_2_versions')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/next'), 43)

    def test_get_latest_upstream_bzr_rev_without_commit_tag(self):
        '''We will get rev 0 if we don't have any commit tag'''
        self.get_data_branch('dummypackage')
        with open("debian/changelog") as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f), 0)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_with_marker_on_two_lines(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa with a marker shown on 2 lines'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_with_marker_two_lines')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/experimental-certified'), 42)

    def test_get_latest_upstream_bzr_rev_with_dest_ppa_with_another_ppa_marker(self):
        '''We always get the latest upstream bzr rev version when we have a dest ppa with another dest ppa marker'''
        with open(os.path.join(self.changelogs_file_dir, 'destppa_with_another_dest_ppa')) as f:
            self.assertEquals(packagemanager.get_latest_upstream_bzr_rev(f, 'ubuntu-unity/next'), 8)

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

    def get_source_files_for_package(self, package_name, for_download=False):
        '''Small handy tool to get a source package files in package_name dir'''
        result_files_path = []
        package_source_dir = self.get_ubuntu_source_content_path(package_name)
        for filename in os.listdir(package_source_dir):
            if for_download:
                filename = urllib.quote(filename)
            result_files_path.append(os.path.join(package_source_dir, filename))
        return result_files_path

    def get_dsc_for_package(self, package_name):
        '''Only return the .dsc file for a package source name'''
        for file in self.get_source_files_for_package(package_name):
            if file.endswith('.dsc'):
                return file

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest(self, launchpadmanagerMock):
        '''We grab the correct source from dest'''

        dest_archive = Mock()
        source1 = Mock()
        dest_archive.getPublishedSources.return_value = [source1]
        source1.sourceFileUrls.return_value = self.get_source_files_for_package('foo_package', for_download=True)

        source_package_dir = packagemanager.get_source_package_from_dest("foo", dest_archive, "42.0daily83.09.13.2-0ubuntu1", "rolling")

        launchpadmanagerMock.get_series.assert_called_once_with("rolling")
        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="42.0daily83.09.13.2-0ubuntu1")
        source1.sourceFileUrls.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_having_multiple_candidates(self, launchpadmanagerMock):
        '''We grab the correct source from dest, even if we have more than once'''

        dest_archive = Mock()
        source1 = Mock()
        source2 = Mock()
        dest_archive.getPublishedSources.return_value = [source1, source2]
        source1.sourceFileUrls.return_value = self.get_source_files_for_package('foo_package')

        source_package_dir = packagemanager.get_source_package_from_dest("foo", dest_archive, "42.0daily83.09.13.2-0ubuntu1", "rolling")

        launchpadmanagerMock.get_series.assert_called_once_with("rolling")
        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="42.0daily83.09.13.2-0ubuntu1")
        source1.sourceFileUrls.assert_called_once()
        self.assertFalse(source2.sourceFileUrls.called)
        self.assertTrue(os.path.isdir(source_package_dir))

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_with_epoc(self, launchpadmanagerMock):
        '''We grab the correct source from dest with epoch'''

        dest_archive = Mock()
        source1 = Mock()
        dest_archive.getPublishedSources.return_value = [source1]
        source1.sourceFileUrls.return_value = self.get_source_files_for_package('foo_package', for_download=True)

        source_package_dir = packagemanager.get_source_package_from_dest("foo", dest_archive, "1:42.0daily83.09.13.2-0ubuntu1", "rolling")

        launchpadmanagerMock.get_series.assert_called_once_with("rolling")
        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="1:42.0daily83.09.13.2-0ubuntu1")
        source1.sourceFileUrls.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))
        self.assertNotIn(':', source_package_dir)

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_for_native(self, launchpadmanagerMock):
        '''We grab the correct source from dest for native packages'''

        dest_archive = Mock()
        source1 = Mock()
        dest_archive.getPublishedSources.return_value = [source1]
        source1.sourceFileUrls.return_value = self.get_source_files_for_package('foo_native_package', for_download=True)

        source_package_dir = packagemanager.get_source_package_from_dest("foo", dest_archive, "42.0daily83.09.13.2", "rolling")

        launchpadmanagerMock.get_series.assert_called_once_with("rolling")
        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="42.0daily83.09.13.2")
        source1.sourceFileUrls.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_with_special_chars(self, launchpadmanagerMock):
        '''We grab the correct source from dest with special chars like ~ and +'''

        dest_archive = Mock()
        source1 = Mock()
        dest_archive.getPublishedSources.return_value = [source1]
        source1.sourceFileUrls.return_value = self.get_source_files_for_package('foo_specialchars_package', for_download=True)

        source_package_dir = packagemanager.get_source_package_from_dest("foo", dest_archive, "42.0~daily83.09.13.2+0-0ubuntu1", "rolling")

        launchpadmanagerMock.get_series.assert_called_once_with("rolling")
        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="42.0~daily83.09.13.2+0-0ubuntu1")
        source1.sourceFileUrls.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_not_published(self, launchpadmanagerMock):
        '''We return none if the package was never published into the dest'''
        self.assertIsNone(packagemanager.get_source_package_from_dest("foo", None, "0", "rolling"))
        self.assertEqual(os.listdir('.'), [])
        self.assertFalse(launchpadmanagerMock.get_series.called)

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_with_ubuntu_native_version(self, launchpadmanagerMock):
        '''We grab the correct source from dest with ubuntu native version'''

        dest_archive = Mock()
        source1 = Mock()
        dest_archive.getPublishedSources.return_value = [source1]
        source1.sourceFileUrls.return_value = self.get_source_files_for_package('foo_native_ubuntu_version', for_download=True)

        source_package_dir = packagemanager.get_source_package_from_dest("foo", dest_archive, "42ubuntu1", "rolling")

        launchpadmanagerMock.get_series.assert_called_once_with("rolling")
        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="42ubuntu1")
        source1.sourceFileUrls.assert_called_once()
        self.assertTrue(os.path.isdir(source_package_dir))

    def test_release_with_no_ubuntu_upload(self):
        '''We release if there has been no upload before'''
        self.assertTrue(packagemanager.is_new_content_relevant_since_old_published_source(None))

    def test_release_if_content_committed_before_snapshot_commit(self):
        '''We release if there is at least one change including an upstream change'''
        self.get_data_branch('oneupstreamchange_before_snapshot_committed')
        dest_version_source = self.get_ubuntu_source_content_path('oneupstreamchange_before_snapshot_committed')
        self.assertTrue(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_release_if_content_committed_and_changelog_unreleased_content(self):
        '''We release if there is at least one change including an upstream change, with a changelog content (UNRELEASED)'''
        self.get_data_branch('oneupstreamchange_with_unreleased_changelog_change')
        dest_version_source = self.get_ubuntu_source_content_path('regular_released_branch')
        self.assertTrue(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_release_if_new_content_with_manual_uploads(self):
        '''We release if there has been some manual uploads backported, but we still have at least one content difference'''
        self.get_data_branch('changebetween_manual_uploads')
        dest_version_source = self.get_ubuntu_source_content_path('2manualuploads')
        self.assertTrue(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_dont_release_if_content_matches(self):
        '''We don't release if the upstream and downstream content matches, even if we had a manual upload to distro'''
        self.get_data_branch('onemanualupload')
        dest_version_source = self.get_ubuntu_source_content_path('onemanualupload')
        self.assertFalse(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_dont_release_if_only_ignore_content(self):
        '''We don't release if the upstream and downstream only have ignored content'''
        self.get_data_branch('onlyignorechanges')
        dest_version_source = self.get_ubuntu_source_content_path('onemanualupload')
        self.assertFalse(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_dont_release_if_vcs_bzr_change(self):
        '''We don't release if there is only a vcs* change (when diverging branches)'''
        self.get_data_branch('vcsbzrchange')
        dest_version_source = self.get_ubuntu_source_content_path('onerelease')
        self.assertFalse(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_dont_release_if_vcs_bzr_change_with_changelog(self):
        '''We don't release if there is only a vcs* change (when diverging branches), even with a changelog change'''
        self.get_data_branch('vcsbzrchangewithchangelog')
        dest_version_source = self.get_ubuntu_source_content_path('onerelease')
        self.assertFalse(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_release_even_if_changelog_change(self):
        '''We release even if the only change is a debian/changelog change'''
        self.get_data_branch('debianchangelog_change_on_onemanualupload')
        dest_version_source = self.get_ubuntu_source_content_path('onemanualupload')
        self.assertTrue(packagemanager.is_new_content_relevant_since_old_published_source(dest_version_source))

    def test_package_wrongly_diffing(self):
        '''We detect if a package only having the automatic bump and marker in debian/changelog has nothing relevant'''
        for file in self.get_source_files_for_package("foo_package"):
            if not os.path.isdir(file):
                shutil.copy2(file, '.')
        dest_version_source = self.get_ubuntu_source_content_path('ubuntu_foo_package_with_one_less_release')
        self.assertFalse(packagemanager.is_relevant_source_diff_from_previous_dest_version("foo_42.0daily83.09.13.2-0ubuntu1.dsc", dest_version_source))

    def test_package_rightly_diffing(self):
        '''We detect if a package has relevant changes justifying the daily release'''
        for file in self.get_source_files_for_package("foo_package"):
            if not os.path.isdir(file):
                shutil.copy2(file, '.')
        dest_version_source = self.get_ubuntu_source_content_path('ubuntu_foo_package_with_two_less_release')
        self.assertTrue(packagemanager.is_relevant_source_diff_from_previous_dest_version("foo_42.0daily83.09.13.2-0ubuntu1.dsc", dest_version_source))

    def test_detect_packaging_changes_since_last_release(self):
        '''We detect packaging changes since last release'''
        self.assertTrue(packagemanager._packaging_changes_between_dsc(self.get_dsc_for_package("foo_package"),
                                                                      self.get_dsc_for_package("foo_package_with_upstream_and_packaging_changes")))

    def test_with_upstream_and_changelog_only_change(self):
        '''We detect no packaging change when a package has the generated upstream and changelog changed only'''
        self.assertFalse(packagemanager._packaging_changes_between_dsc(self.get_dsc_for_package("foo_package"),
                                                                       self.get_dsc_for_package("foo_package_with_upstream_changes")))

    def test_always_diff_when_no_previous_version_in_distro(self):
        '''We detect packaging change if no previous version was in distro'''
        self.assertTrue(packagemanager._packaging_changes_between_dsc(None, self.get_dsc_for_package("foo_package")))

    def test_generate_diff(self):
        '''We generate the right diff'''
        packagemanager.generate_diff_between_dsc("foo.diff", self.get_dsc_for_package("foo_package"),  self.get_dsc_for_package("foo_package_with_upstream_and_packaging_changes"))
        canonical_filepath = os.path.join(self.data_dir, "results", "foo_package_foo_package_with_upstream_and_packaging_changes.diff")
        self.assertFilesAreIdenticals("foo.diff", canonical_filepath)

    def test_diff_warn_for_new_package(self):
        '''We warn in the generate diff for new packages'''
        packagemanager.generate_diff_between_dsc("foo.diff", None,  self.get_dsc_for_package("foo_package"))
        canonical_filepath = os.path.join(self.data_dir, "results", "new_foo_package.diff")
        self.assertFilesAreIdenticals("foo.diff", canonical_filepath)

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_regular(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830912-0ubuntu1', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_epoch(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version but having an epoch'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('1:42+13.10.19830912-0ubuntu1', '13.10'), '1:42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_manual_upload(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version but having a previous manual upload'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830912-0ubuntu3', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_first_rerelease_sameday(self, datetimeMock):
        '''We create a new packaging version after an already first released version the same day'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830913-0ubuntu1', '13.10'), '42+13.10.19830913.1-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_continous_rerelease_sameday(self, datetimeMock):
        '''We create a new packaging version after an already more than one released version the same day'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830913.2-0ubuntu1', '13.10'), '42+13.10.19830913.3-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_manual_upload_same_day(self, datetimeMock):
        '''We create a new packaging version after an already released version the same day with some manual uploads'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830913.2-0ubuntu3', '13.10'), '42+13.10.19830913.3-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_transition_releases(self, datetimeMock):
        '''We create a new packaging version after an old regular daily release version transitionning from one release to another one'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.04.19830913-0ubuntu1', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_without_daily(self, datetimeMock):
        '''We create a new packaging version after a normal (non daily) released version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42-0ubuntu1', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_native(self, datetimeMock):
        """Verify that native package versions are supported."""
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version(
            '13.10+13.10.19830912', '13.10'),
                         '13.10+13.10.19830913')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_native_epoch(self, datetimeMock):
        """Verify that native package versions with epoch are supported."""
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version(
            '1:13.10+13.10.19830912', '13.10'),
                         '1:13.10+13.10.19830913')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_native_first_rerelease_sameday(
            self, datetimeMock):
        """Verify that native versions re-release on same day is supported."""
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version(
            '13.10+13.10.19830913', '13.10'),
                         '13.10+13.10.19830913.1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_native_continous_rerelease_sameday(
            self, datetimeMock):
        """Verify that native versions continuoed re-release is supported."""
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version(
            '13.10+13.10.19830913.2', '13.10'),
                         '13.10+13.10.19830913.3')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_native_ppa_dest(self, datetimeMock):
        """Verify that native versions with a ppa dest are supported."""
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version(
            '13.10+13.10.19830912', '13.10', 'didrocks/my-ppa_mine'),
                         '13.10+13.10.19830913didrocks.my.ppa.mine')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_native(self, datetimeMock):
        '''We create a new packaging version after a native released version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_sync_debian(self, datetimeMock):
        '''We create a new packaging version after a synced version from debian'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42-1', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_debian_based_manual(self, datetimeMock):
        '''We create a new packaging version after a manual based on a debian version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42-1ubuntu2', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_debian_based_daily(self, datetimeMock):
        '''We create a new packaging version after a manual based on a debian version'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830912-1ubuntu2', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_with_ppa_dest(self, datetimeMock):
        '''We create a new packaging version after with a ppa destination not being distro'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830912-0ubuntu1', '13.10', 'didrocks/my-ppa_mine'), '42+13.10.19830913didrocks.my.ppa.mine-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_with_ppa_dest_after_a_ppa_dest(self, datetimeMock):
        '''We create a new packaging version after with a ppa destination not being distro after another ppa_dest'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830912didrocks.my.ppa.mine-0ubuntu1', '13.10', 'didrocks/my-ppa_mine'), '42+13.10.19830913didrocks.my.ppa.mine-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_with_ppa_dest_after_a_ppa_dest_with_intermediate_version(self, datetimeMock):
        '''We create a new packaging version after with a ppa destination not being distro after another ppa_dest released the same day'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830913didrocks.my.ppa.mine-0ubuntu1', '13.10', 'didrocks/my-ppa_mine'), '42+13.10.19830913.1didrocks.my.ppa.mine-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_with_ppa_dest_to_distro(self, datetimeMock):
        '''We create a new packaging version after having a ppa destination to normal distro'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42+13.10.19830912didrocks.my.ppa.mine-0ubuntu1', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_wrong_native(self, datetimeMock):
        '''We create a new packaging version after a wrong native with ubuntu in it'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42ubuntu1', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_old_format(self, datetimeMock):
        '''We create a new packaging version transitionned from previous daily format'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.12-1ubuntu2', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_old_format_complex(self, datetimeMock):
        '''We create a new packaging version transitionned from previous daily format with maintenance branch'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.12~13.10-1ubuntu2', '13.10'), '42+13.10.19830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_old_format_sameday(self, datetimeMock):
        '''We create a new packaging version transitionned from previous daily format while releasing on the same day'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '20830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.13~13.10-1ubuntu2', '13.10'), '42+13.10.20830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_old_format_sameday_with_minor(self, datetimeMock):
        '''We create a new packaging version transitionned from previous daily format while releasing on the same day after multiple releases'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '20830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.13.3~13.10-1ubuntu2', '13.10'), '42+13.10.20830913-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

    @patch('cupstream2distro.packagemanager.datetime')
    def test_create_new_packaging_version_from_old_format_with_maintenance_branch(self, datetimeMock):
        '''We create a new packaging version transitionned from previous daily format with feature branch'''
        strftime_call = datetimeMock.date.today.return_value.strftime
        strftime_call.side_effect = lambda date: '19830913'
        self.assertEqual(packagemanager.create_new_packaging_version('42daily83.09.12didrocks.my.ppa.mine-0ubuntu2', '13.10', 'didrocks/my-ppa_mine'), '42+13.10.19830913didrocks.my.ppa.mine-0ubuntu1')
        strftime_call.assert_called_with('%Y%m%d')

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
        with open(os.path.join(self.changelogs_file_dir, 'different_bugs_pattern')) as f:
            self.assertEquals(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['56789', '67890', '34567', '12345',
                                                                                                             '567890', '678901', '123456', '1234567']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_no_bugs(self):
        '''We collect bugs in the changelog file until latest snapshot. No bugs, but an unreleased changelog'''
        source_branch = self.get_origin_branch_path("basic")
        with open(os.path.join(source_branch, 'debian', 'changelog')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set())

    def test_collect_bugs_in_changelog_until_latest_snapshot_no_unrelease_no_manual(self):
        '''We collect bugs in the changelog file until latest snapshot. No manual upload, no unreleased changelog'''
        with open(os.path.join(self.changelogs_file_dir, 'no_unrelease_no_manual')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set())

    def test_collect_bugs_in_changelog_until_latest_snapshot_multiple_unrelease(self):
        '''We collect bugs in the changelog file until latest snapshot, but no bug from it the first snapshot. Only multiple unreleased changelog content'''
        with open(os.path.join(self.changelogs_file_dir, 'multiple_unrelease')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['34567', '12345', '23456']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_multiple_unrelease_manual_upload(self):
        '''Test that we collect bugs in the changelog file until latest snapshot. We only collect bugs until the last manual upload'''
        with open(os.path.join(self.changelogs_file_dir, 'multiple_unrelease_with_release')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['23456']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_only_one_unreleased_changelog(self):
        '''Test that we collect bugs in the changelog file until latest snapshot. We collect the bugs from the one unreleased changelog'''
        with open(os.path.join(self.changelogs_file_dir, 'one_unreleased')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set(['12345']))

    def test_collect_bugs_in_changelog_until_latest_snapshot_only_one_unreleased_changelog_no_bug(self):
        '''Test that we collect bugs in the changelog file until latest snapshot. We have no bug from the only one unreleased changelog'''
        with open(os.path.join(self.changelogs_file_dir, 'one_unreleased_no_bug')) as f:
            self.assertEqual(packagemanager.collect_bugs_in_changelog_until_latest_snapshot(f, "foo"), set())

    def test_update_changelog_simple(self):
        '''Update a changelog from a list of one author with a known bug and bzr rev'''
        self.get_data_branch('dummypackage')
        authors = {"Foo": ["One fix for LP: #12345"]}
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "simple_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_simple_no_author(self):
        '''Update a changelog from a list with no bug fix'''
        self.get_data_branch('dummypackage')
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, {})
        result_file = os.path.join(self.result_dir, "no_bug_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_one_author_multiple_bugs(self):
        '''Update a changelog from a list of one author with multiple bugs'''
        self.get_data_branch('dummypackage')
        authors = {"Foo": ["One fix for LP: #12345", "Another fix for LP: #23456"]}
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "multiple_bugs_one_author_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_multiple_authors(self):
        '''Update a changelog from a list of multiple authors with multiple bugs'''
        self.get_data_branch('dummypackage')
        authors = {"Foo": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("1.2daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "multiple_authors_bugs_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_with_msg_starting_with_dash(self):
        '''Update a changelog with a message starting with '-'.'''
        self.get_data_branch('basic')
        authors = {"Foo": ["- One fix for LP: #12345"]}
        packagemanager.update_changelog("42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "message_starting_with_dash")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_with_existing_content(self):
        '''Update a changelog when we already have existing content'''
        self.get_data_branch('basic')
        authors = {"Foo": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "existing_content_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_with_existing_content_existing_author(self):
        '''Update a changelog when we already have existing content and author'''
        self.get_data_branch('basic')
        authors = {"Didier Roche": ["One fix for LP: #12345", "Another fix for LP: #23456"], "Bar": ["Another fix for LP: #23456"], "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog("42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(self.result_dir, "existing_content_author_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_with_existing_content_existing_multiple_authors(self):
        '''Update a changelog when we already have existing content and multiple existing authors'''
        self.get_data_branch('basic_multiple_contents')
        authors = {"Didier Roche": ["One fix for LP: #12345",
                                    "Another fix for LP: #23456"],
                   "Bar": ["Another fix for LP: #23456"],
                   "Baz baz": ["and another Fix on LP: #34567"]}
        packagemanager.update_changelog(
            "42.0daily83.09.14-0ubuntu1", "raring", 42, authors)
        result_file = os.path.join(
            self.result_dir,
            "existing_content_multiple_authors_changelog_update")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")

    def test_update_changelog_with_dest_ppa(self):
        '''Update a changelog from a list with a destination ppa'''
        self.get_data_branch('dummypackage')
        packagemanager.update_changelog("1.2daily83.09.14.ubuntu.unity.next-0ubuntu1", "raring", 42, {}, "ubuntu-unity/next")
        result_file = os.path.join(self.result_dir, "changelog_with_dest_ppa")
        self.assertChangelogFilesAreIdenticals(result_file, "debian/changelog")


class PackageManagerOfflineTests(BaseUnitTestCase):
    '''Test that can be used for system test, but not depending on online service'''

    def test_refresh_symbols_files_simple(self):
        '''Update the symbols file with the new version'''
        self.get_data_branch('basic_symbols')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_symbols = os.path.join(self.result_dir, "simple_update.symbols")
        result_changelog = os.path.join(self.result_dir,
                                        "simple_update.changelog")
        self.assertFilesAreIdenticals("debian/foo.symbols", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        self.assertEqual(
            subprocess.Popen(['bzr', 'revno'],
                             stdout=subprocess.PIPE).communicate()[0], "8\n")

    def test_refresh_symbols_files_multiple_replace_tag_in_symbol(self):
        '''Update the symbols file having multiple replace tag with the new version'''
        self.get_data_branch('symbols_with_multiple_replace')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_symbols = os.path.join(self.result_dir, "multiplesymbols_update.symbols")
        result_changelog = os.path.join(self.result_dir, "simple_update.changelog")
        self.assertFilesAreIdenticals("debian/foo.symbols", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        self.assertEqual(subprocess.Popen(['bzr', 'revno'], stdout=subprocess.PIPE).communicate()[0], "8\n")

    def test_refresh_symbols_files_simple_with_existing_changelog(self):
        '''Update the symbols file with the new version having an existing changelog'''
        self.get_data_branch('basic_symbols_with_changelog')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_symbols = os.path.join(self.result_dir, "simple_update.symbols")
        result_changelog = os.path.join(self.result_dir, "simple_update_with_existing_content.changelog")
        self.assertFilesAreIdenticals("debian/foo.symbols", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        self.assertEqual(subprocess.Popen(['bzr', 'revno'], stdout=subprocess.PIPE).communicate()[0], "8\n")

    def test_refresh_symbols_files_with_no_symbol_files(self):
        '''Update the symbols file with the new version having no symbol file'''
        self.get_data_branch('simple')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_changelog = os.path.join(self.data_dir, "branches", "simple", "debian", "changelog")
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        # 8 is tip on "simple branch" means no commit done
        self.assertEqual(subprocess.Popen(['bzr', 'revno'], stdout=subprocess.PIPE).communicate()[0], "8\n")

    def test_refresh_symbols_files_with_no_symbol_files_to_update(self):
        '''No update for symbols files having nothing to be updated for'''
        self.get_data_branch('no_symbols_to_update')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_changelog = os.path.join(self.data_dir, "branches", "no_symbols_to_update", "debian", "changelog")
        result_symbols = os.path.join(self.data_dir, "branches", "no_symbols_to_update", "debian", "foo.symbols")
        self.assertFilesAreIdenticals("debian/foo.symbols", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "2"
        self.assertEqual(subprocess.Popen(['bzr', 'revno'], stdout=subprocess.PIPE).communicate()[0], "7\n")

    def test_refresh_symbols_files_with_multiple_symbol_files(self):
        '''Update all the symbols file with the new version'''
        self.get_data_branch('multiple_symbols_with_changelog')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_symbols = os.path.join(self.result_dir, "multiplesymbols_update.symbols")
        result_changelog = os.path.join(self.result_dir, "simple_update.changelog")
        self.assertFilesAreIdenticals("debian/foo.symbols", result_symbols)
        self.assertFilesAreIdenticals("debian/bar.symbols", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        self.assertEqual(subprocess.Popen(['bzr', 'revno'], stdout=subprocess.PIPE).communicate()[0], "8\n")

    def test_dont_refresh_symbols_files_for_random_file(self):
        '''We don't update random files having the magic replace stenza'''
        self.get_data_branch('multiple_symbols_with_changelog')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        original_install_file = os.path.join(self.data_dir, "branches", "multiple_symbols_with_changelog", "debian", "install")
        self.assertFilesAreIdenticals(original_install_file, "debian/install")

    def test_refresh_symbols_files_alone_symbol(self):
        '''Update a symbols (not <package>.symbols) file'''
        self.get_data_branch('basic_alone_symbols')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_symbols = os.path.join(self.result_dir, "simple_update.symbols")
        result_changelog = os.path.join(self.result_dir, "simple_update.changelog")
        self.assertFilesAreIdenticals("debian/symbols", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        self.assertEqual(subprocess.Popen(['bzr', 'revno'], stdout=subprocess.PIPE).communicate()[0], "8\n")

    def test_refresh_symbols_files_with_arch_file(self):
        '''Update the symbols file with the new version'''
        self.get_data_branch('basic_arch_symbols')
        packagemanager.refresh_symbol_files('42.0daily83.09.14-0ubuntu1')
        result_symbols = os.path.join(self.result_dir, "simple_update.symbols")
        result_changelog = os.path.join(self.result_dir,
                                        "simple_update.changelog")
        self.assertFilesAreIdenticals("debian/foo.symbols.amd64", result_symbols)
        self.assertChangelogFilesAreIdenticals(result_changelog,
                                               "debian/changelog")
        os.environ["MOCK_MODE"] = "1"
        self.assertEqual(
            subprocess.Popen(['bzr', 'revno'],
                             stdout=subprocess.PIPE).communicate()[0], "8\n")


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
    def test_build_source_package_with_ppa(self, settings_mock):
        '''Call cowbuilder and build a source package with a ppa (unsigned for tests)'''
        self.setup_settings_mock(settings_mock)
        self.get_data_branch('dummypackage')
        os.environ["MOCK_MODE"] = "1"
        packagemanager.build_source_package("raring", "1.1-0ubuntu1", "ubuntu-unity/next")
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

    def get_source_files_for_package(self, package_name):
        '''Small handy tool to get a source package files in package_name dir'''
        result_files_path = []
        package_source_dir = self.get_ubuntu_source_content_path(package_name)
        for filename in os.listdir(package_source_dir):
            result_files_path.append(os.path.join(package_source_dir, filename))
        return result_files_path

    def test_raise_exception_when_upload_fail(self):
        '''We fail if the dput push failed'''
        with self.assertRaises(Exception):
            packagemanager.upload_package('foo', '1:83.09.13-0ubuntu1', 'didrocks/foo')

    def test_raise_exception_if_diff_unexisting_dsc(self):
        '''We raise an exception if we try to debdiff an unexisting dsc'''
        with self.assertRaises(Exception):
            packagemanager._packaging_changes_between_dsc("foo.dsc", "bar.dsc")

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_no_source(self, launchpadmanagerMock):
        '''Assert when we can't find the correct source in dest we try to download'''

        dest_archive = Mock()
        dest_archive.getPublishedSources.return_value = []
        with self.assertRaises(Exception):
            packagemanager.get_source_package_from_dest("foo", dest_archive, "42.0daily83.09.13.2", "rolling")

    @patch('cupstream2distro.packagemanager.launchpadmanager')
    def test_get_source_package_from_dest_wrong_content_source(self, launchpadmanagerMock):
        '''Assert when we didn't download properly expected source (in this case, no .dsc file)'''

        def get_source_files_for_package_but_dsc(package_name):
            '''Small handy tool to get a source package files in package_name dir'''
            result_files_path = []
            package_source_dir = self.get_ubuntu_source_content_path(package_name)
            for filename in os.listdir(package_source_dir):
                if not filename.endswith('.dsc'):
                    result_files_path.append(os.path.join(package_source_dir, filename))
            return result_files_path

        dest_archive = Mock()
        source1 = Mock()
        dest_archive.getPublishedSources.return_value = [source1]
        source1.sourceFileUrls.return_value = get_source_files_for_package_but_dsc('foo_package')

        with self.assertRaises(Exception):
            packagemanager.get_source_package_from_dest("foo", dest_archive, "42.0daily83.09.13.2-0ubuntu1", "rolling")

        dest_archive.getPublishedSources.assert_called_once_with(status="Published", exact_match=True, source_name="foo", distro_series=launchpadmanagerMock.get_series.return_value, version="42.0daily83.09.13.2-0ubuntu1")
        source1.sourceFileUrls.assert_called_once()

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
