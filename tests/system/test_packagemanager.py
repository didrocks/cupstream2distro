# -*- coding: utf-8 -*-
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

from ..unit.test_packagemanager import PackageManagerOnlineTests, PackageManagerOnlineTestsWithErrors, PackageManagerOfflineTests
from . import BaseSystemTestCase


class SystemPackageManagerOnlineTests(BaseSystemTestCase, PackageManagerOnlineTests):
    '''Same tests than unit PackageManagerOnlineTests, but with system cowbuilder'''


class SystemPackageManagerOnlineTestsWithErrors(BaseSystemTestCase, PackageManagerOnlineTestsWithErrors):
    '''Same tests than unit PackageManagerOnlineTestsWithErrors, but with system cowbuilder'''


class SystemPackageManagerOfflineTests(BaseSystemTestCase, PackageManagerOfflineTests):
    '''Same tests than unit ackageManagerOfflineTests, but with system components'''
