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

from ..unit.test_packagemanager import PackageManagerOnlineTests, PackageManagerOnlineTestsWithErrors
from ..unit import BaseUnitTestCase

from cupstream2distro import packagemanager


class PackageManagerOnlineTests(PackageManagerOnlineTests):
    '''Same tests than unit PackageManagerOnlineTests, but with system cowbuilder'''

    @classmethod
    def setUpClass(cls):
        ## bypass setup from BaseUnitTestCase
        super(BaseUnitTestCase, cls).setUpClass()
        cls.original_settings = packagemanager.settings


class PackageManagerOnlineTestsWithErrors(PackageManagerOnlineTestsWithErrors):
    '''Same tests than unit PackageManagerOnlineTestsWithErrors, but with system cowbuilder'''

    @classmethod
    def setUpClass(cls):
        ## bypass setup from BaseUnitTestCase
        super(BaseUnitTestCase, cls).setUpClass()
        cls.original_settings = packagemanager.settings
