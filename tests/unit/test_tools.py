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

from cupstream2distro import tools

import os
import shutil


class ToolsTests(BaseUnitTestCase):

    def setUp(self):
        '''add some default files'''
        super(ToolsTests, self).setUp()
        self.artefacts_dir = os.path.join(self.data_dir, 'artefacts')

    def test_get_previous_distro_version_from_config(self):
        '''We load and return the previous distro version from config'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        self.assertEquals(tools.get_previous_distro_version_from_config('foo'), '6.12.0-0ubuntu1')

    def test_return_exception_if_config_doesnt_exist(self):
        '''We return an exception if the config files does not exist'''
        with self.assertRaises(Exception):
            tools.get_previous_distro_version_from_config('foo')

    def test_save_correct_project_file(self):
        '''We save the correct profiles file'''
        tools.save_project_config('foo', 'lp:foo', '6.12.0-0ubuntu1', '6.12.0daily13.02.27-0ubuntu1')
        self.assertFilesAreIdenticals('foo.project', os.path.join(self.project_file_dir, 'foo.project'))

    def test_packaging_diff_filename(self):
        '''Return the right packaging diff name'''
        self.assertEquals(tools.get_packaging_diff_filename("foo", "1.0daily~-0ubuntu1"), "packaging_changes_foo_1.0daily~-0ubuntu1.diff")

    def test_generate_xml_artefacts_no_issue(self):
        '''Generate the xml jenkins artefacts when no issue occured'''
        tools.generate_xml_artefacts("Test Name", [], 'file.xml')
        self.assertFilesAreIdenticals('file.xml', os.path.join(self.artefacts_dir, 'nofailure.xml'))

    def test_generate_xml_artefacts_one_failure(self):
        '''Generate the xml jenkins artefacts when there is one failure'''
        tools.generate_xml_artefacts("Test Name", ["one issue"], 'file.xml')
        self.assertFilesAreIdenticals('file.xml', os.path.join(self.artefacts_dir, 'onefailure.xml'))

    def test_generate_xml_artefacts_two_failures(self):
        '''Generate the xml jenkins artefacts when there is more than one failure'''
        tools.generate_xml_artefacts("Test Name", ["one issue", "a second issue"], 'file.xml')
        self.assertFilesAreIdenticals('file.xml', os.path.join(self.artefacts_dir, 'twofailures.xml'))
