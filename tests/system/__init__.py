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


import os

from ..tools import basetestcase


class BaseSystemTestCase(basetestcase.BaseTestCase):
    '''Base system test case module, remove all mocks from PATH

    Note that BaseSystemTestCase cleanswap the double BranchHandlingTests import (with PATH change) due to nosetests.
    So we need it to be inherited *first* by subclasses to be the last executed'''

    @classmethod
    def setUpClass(cls):
        super(BaseSystemTestCase, cls).setUpClass()
        cls.removeFromPath(os.path.join("mocks", "offline"))
        cls.removeFromPath(os.path.join("mocks", "online"))


class BaseSystemTestCaseWithErrors(BaseSystemTestCase):
    '''Base system test case module, simulating errors in mock objects'''

    def setUp(self):
        '''Reset the error mode to 1'''
        super(BaseSystemTestCaseWithErrors, self).setUp()
        os.environ['MOCK_ERROR_MODE'] = "1"

    @classmethod
    def tearDownClass(cls):
        super(BaseSystemTestCaseWithErrors, cls).setUpClass()
        try:
            os.environ.pop('MOCK_ERROR_MODE')
        except:
            pass
