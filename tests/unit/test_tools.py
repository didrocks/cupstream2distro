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

from . import BaseUnitTestCase

from cupstream2distro import tools

import os
import shutil


class MockMerge:
    def __init__(self, source_branch, prereq_branch=None):
        self.source_branch = MockBranch(source_branch)
        if prereq_branch:
            self.prerequisite_branch = MockBranch(prereq_branch)
        else:
            self.prerequisite_branch = None

class MockBranch:
    def __init__(self, bzr_identity):
        self.bzr_identity = bzr_identity
    
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
        tools.save_project_config('foo', 'lp:foo', '42', '6.12.0-0ubuntu1', '6.12.0daily13.02.27-0ubuntu1')
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

    def test_mark_project_as_published(self):
        '''Rename current project filename once published to the unique project file to not republish it'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        tools.mark_project_as_published('foo', '4.2dailysomething-0ubuntu1')
        self.assertTrue(os.path.isfile('foo.project_4.2dailysomething-0ubuntu1'))

    def test_mark_project_and_diff_as_published(self):
        '''Rename current project filename and diff file once published to the unique project file to not republish them'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), 'packaging_changes_foo_4.2dailysomething-0ubuntu1.diff')
        tools.mark_project_as_published('foo', '4.2dailysomething-0ubuntu1')
        self.assertTrue(os.path.isfile('packaging_changes_foo_4.2dailysomething-0ubuntu1.diff.published'))

    def test_no_project_published(self):
        '''Get no project published if nothing is published'''
        self.assertEquals(tools.get_published_to_distro_projects(), {})

    def test_one_project_published(self):
        '''Get one project published with one version'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        tools.mark_project_as_published('foo', '42-0ubuntu1')
        self.assertEquals(tools.get_published_to_distro_projects(), {'foo': ['42-0ubuntu1']})

    def test_one_project_published_multiple_times(self):
        '''Get one project published with multiple published versions'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        tools.mark_project_as_published('foo', '42-0ubuntu1')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        tools.mark_project_as_published('foo', '43-0ubuntu1')
        self.assertDictEqual(tools.get_published_to_distro_projects(), {'foo': ['43-0ubuntu1', '42-0ubuntu1']})

    def test_multiple_projects_published(self):
        '''Get one project published with multiple published versions'''
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), '.')
        tools.mark_project_as_published('foo', '42-0ubuntu1')
        shutil.copy2(os.path.join(self.project_file_dir, 'foo.project'), 'bar.project')
        tools.mark_project_as_published('bar', '43-0ubuntu1')
        self.assertDictEqual(tools.get_published_to_distro_projects(), {'foo': ['42-0ubuntu1'], 'bar': ['43-0ubuntu1']})

    def test_parse_and_clean_entry_space(self):
        '''Get an entry only separated by spaces'''
        self.assertEqual(tools.parse_and_clean_entry("foo1 foo2 foo3"),
                         ["foo1", "foo2", "foo3"])

    def test_parse_and_clean_entry_comma(self):
        '''Get an entry only separated by commas'''
        self.assertEqual(tools.parse_and_clean_entry("foo1, foo2, foo3"),
                         ["foo1", "foo2", "foo3"])

    def test_parse_and_clean_entry_comma_and_spaces(self):
        '''Get an entry only separated with a sep (commas) and a lot of additional spaces'''
        self.assertEqual(tools.parse_and_clean_entry("    foo1,    foo2  , foo3"),
                         ["foo1", "foo2", "foo3"])


    def test_parse_and_clean_entry_slash(self):
        '''Get an entry only separated by slash'''
        self.assertEqual(tools.parse_and_clean_entry("foo1/foo2/foo3", slash_as_sep=True),
                         ["foo1", "foo2", "foo3"])

    def test_parse_and_clean_entry_return(self):
        '''Get an entry only separated by commas and space'''
        self.assertEqual(tools.parse_and_clean_entry("foo1\nfoo2\nfoo3"),
                         ["foo1", "foo2", "foo3"])

    def test_parse_and_clean_entry_all_sep_but_slash(self):
        '''Get an entry only separated by all possible sep'''
        self.assertEqual(tools.parse_and_clean_entry("foo1, foo2\nfoo3\n foo4"),
                         ["foo1", "foo2", "foo3", "foo4"])

    def test_parse_and_clean_entry_all_sep(self):
        '''Get an entry only separated by all possible sep'''
        self.assertEqual(tools.parse_and_clean_entry("foo1, foo2\nfoo3\n foo4 / foo5  ", slash_as_sep=True),
                         ["foo1", "foo2", "foo3", "foo4", "foo5"])

    def test_parse_and_clean_entry_no_slash_sep(self):
        '''Get an entry only separated by commas. Entries contains slash and shouldn't be separated'''
        self.assertEqual(tools.parse_and_clean_entry("fo/o1, foo2, foo3"),
                         ["fo/o1", "foo2", "foo3"])

    def test_reorder_branches_regarding_prereqs(self):
        '''Check reorder projects according to prerequisite branches'''
        original_component_list = [ MockMerge("0"), MockMerge("2", "1"), MockMerge("1"), MockMerge("4"), MockMerge("3", "2") ]
        resulting_component_list = tools.reorder_branches_regarding_prereqs(original_component_list)
        self.assertEqual(len(resulting_component_list), 5)
        self.assertEqual(resulting_component_list[0].source_branch.bzr_identity, "0")
        self.assertEqual(resulting_component_list[1].source_branch.bzr_identity, "1")
        self.assertEqual(resulting_component_list[2].source_branch.bzr_identity, "2")
        self.assertEqual(resulting_component_list[3].source_branch.bzr_identity, "3")
        self.assertEqual(resulting_component_list[4].source_branch.bzr_identity, "4")

    def test_reorder_branches_regarding_prereqs_no_change(self):
        '''Check that no reorder happens when there are no prerequisite branches used'''
        original_component_list = [ MockMerge("1"), MockMerge("2"), MockMerge("3") ]
        resulting_component_list = tools.reorder_branches_regarding_prereqs(original_component_list)
        self.assertEqual(len(resulting_component_list), 3)
        self.assertEqual(resulting_component_list[0].source_branch.bzr_identity, "1")
        self.assertEqual(resulting_component_list[1].source_branch.bzr_identity, "2")
        self.assertEqual(resulting_component_list[2].source_branch.bzr_identity, "3")
