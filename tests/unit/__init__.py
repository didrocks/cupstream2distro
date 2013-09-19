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


import os

from ..tools import basetestcase


class BaseUnitTestCase(basetestcase.BaseTestCase):
    '''Base unit test case module, add all mocks to PATH'''

    @classmethod
    def setUpClass(cls):
        super(BaseUnitTestCase, cls).setUpClass()
        cls.addToPath(os.path.join("mocks", "offline"))
        cls.addToPath(os.path.join("mocks", "online"))

    def setUp(self):
        super(BaseUnitTestCase, self).setUp()
        self.create_temp_workdir()
        os.environ['MOCK_MODE'] = "0"


class BaseUnitTestCaseWithErrors(BaseUnitTestCase):
    '''Base unit test case module, simulating errors in mock objects'''

    def setUp(self):
        '''Reset the error mode to 1'''
        super(BaseUnitTestCaseWithErrors, self).setUp()
        os.environ['MOCK_ERROR_MODE'] = "1"

    @classmethod
    def tearDownClass(cls):
        super(BaseUnitTestCase, cls).setUpClass()
        try:
            os.environ.pop('MOCK_ERROR_MODE')
        except:
            pass
