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
        self.get_data_branch('neverreleased')
        self.assertTrue(packagemanager.is_new_release_needed(2, 1, "foo", ubuntu_version_source=None))


class PackageManagerTestsWithErrors(BaseUnitTestCaseWithErrors):
    pass
