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

from __future__ import unicode_literals

from launchpadlib.launchpad import Launchpad
import lazr
launchpad = None


def get_launchpad(use_staging=True):
    '''Get THE Launchpad'''
    global launchpad
    if not launchpad:
        if use_staging:
            server = 'staging'
        else:
            server = 'production'
        launchpad = Launchpad.login_with('ps2distro', server, allow_access_levels=["WRITE_PRIVATE"])

    return launchpad


def get_bugs_titles(author_bugs):
    lp = get_launchpad()
    author_bugs_with_title = author_bugs.copy()
    for author in author_bugs:
        bug_title_sets = set()
        for bug in author_bugs[author]:
            try:
                bug_title_sets.add("{} (LP: #{})".format(lp.bugs[bug].title, bug))
            except KeyError:
                # still list non existing or if launchpad timeouts bugs
                bug_title_sets.add(u"Fix LP: #{}".format(bug))
        author_bugs_with_title[author] = bug_title_sets

    return author_bugs_with_title


def open_bugs_for_source(bugs_list, source_name, serie_name):
    lp = get_launchpad()
    ubuntu = lp.distributions['ubuntu']

    # don't nominate for current serie
    if ubuntu.current_series.name == serie_name:
        package = ubuntu.getSourcePackage(name=source_name)
    else:
        serie = ubuntu.getSeries(name_or_version=serie_name)
        package = serie.getSourcePackage(name=source_name)

    for bug_num in bugs_list:
        try:
            bug = lp.bugs[bug_num]
            bug.addTask(target=package)
            bug.lp_save()
        except (KeyError, lazr.restfulclient.errors.BadRequest):
            pass  # ignore non existing or available bugs
