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

from . import BaseUnitTestCase

from cupstream2distro import packageinppamanager

import os
import shutil


class PackageInPPAManagerTests(BaseUnitTestCase):

    def test_get_current_distro_version_from_config(self):
        '''We load and return the current package version from config'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        self.assertEquals(packageinppamanager._get_current_packaging_version_from_config('foo'), '6.12.0daily13.02.27-0ubuntu1')

    def test_get_current_return_from_config(self):
        '''We load and return the current tip rev from config'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        self.assertEquals(packageinppamanager._get_current_rev_from_config('foo'), '42')
