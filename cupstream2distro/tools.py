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

from xml.sax.saxutils import quoteattr, escape

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
