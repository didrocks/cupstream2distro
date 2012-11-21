# -*- coding: UTF8 -*-
# Copyright (C) 2012 Canonical
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

import ConfigParser
import os
import yaml
from xml.sax.saxutils import quoteattr, escape

from .settings import CONFIG_STACK_DIR

WRAPPER_STRING = '''<testsuite errors="0" failures="{}" name="" tests="1" time="0.1">
  <testcase classname="MarkUnstable" name={} time="0.0">{}</testcase>
</testsuite>'''


def generate_xml_artefacts(test_name, details, filename):
    '''Generate a fake test name xml result for marking the build as unstable'''
    failure = ""
    errnum = 0
    if details:
        errnum = 1
        failure = '''
    <failure type="exception">{}</failure>
'''.format(escape(details))

    with open(filename, 'w') as f:
        f.write(WRAPPER_STRING.format(errnum, quoteattr(test_name), failure))


def get_allowed_projects():
    '''Get all projects allowed to be upload'''

    projects = []
    for file in os.listdir(CONFIG_STACK_DIR):
        if not file.endswith(".cfg"):
            continue
        with open(os.path.join(CONFIG_STACK_DIR, file), 'r') as f:
            cfg = yaml.load(f)
            if not 'stack' in cfg or not 'projects' in cfg['stack']:
                continue
            projects_list = cfg['stack']['projects']
            if not projects_list:
                continue
            # items of projects_list can be: ["proj1", "proj2"] or ["proj1": "lp:projet1/name", …]
            for project in projects_list:
                if type(project) is dict:
                    projects.append(project.keys()[0])
                else:
                    projects.append(project)
    return set(projects)


def save_config_for_publish(source_package_name, branch, previous_packaging_version):
    '''Save branch configuration'''
    config = ConfigParser.RawConfigParser()
    config.add_section('Branch')
    config.set('Branch', 'branch', branch)
    config.add_section('Package')
    config.set('Package', 'previous_packaging_version', previous_packaging_version)
    with open("{}.config".format(source_package_name), 'wb') as configfile:
        config.write(configfile)
