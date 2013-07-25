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
# details.cat
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from __future__ import unicode_literals

from launchpadlib.launchpad import Launchpad
import lazr
import logging
import os
launchpad = None

from .settings import ARCHS_TO_EVENTUALLY_IGNORE, VIRTUALIZED_PPA_ARCH, CRED_FILE_PATH, COMMON_LAUNCHPAD_CACHE_DIR


def get_launchpad(use_staging=False, use_cred_file=os.path.expanduser(CRED_FILE_PATH)):
    '''Get THE Launchpad'''
    global launchpad
    if not launchpad:
        if use_staging:
            server = 'staging'
        else:
            server = 'production'

        # as launchpadlib isn't multiproc, fiddling the cache dir if any
        launchpadlib_dir = os.getenv("JOB_NAME")
        if launchpadlib_dir:
            launchpadlib_dir = os.path.join(COMMON_LAUNCHPAD_CACHE_DIR, launchpadlib_dir)

        if use_cred_file:
            launchpad = Launchpad.login_with('cupstream2distro', server, allow_access_levels=["WRITE_PRIVATE"],
                                             version='devel',  # devel because copyPackage is only available there
                                             credentials_file=use_cred_file,
                                             launchpadlib_dir=launchpadlib_dir)
        else:
            launchpad = Launchpad.login_with('cupstream2distro', server, allow_access_levels=["WRITE_PRIVATE"],
                                             version='devel',  # devel because copyPackage is only available there
                                             launchpadlib_dir=launchpadlib_dir)

    return launchpad


def get_ubuntu():
    '''Get the ubuntu distro'''
    lp = get_launchpad()
    return lp.distributions['ubuntu']


def get_ubuntu_archive():
    '''Get the ubuntu main archive'''
    return get_ubuntu().main_archive


def get_series(series_name):
    '''Return the launchpad object for the requested series'''
    return get_ubuntu().getSeries(name_or_version=series_name)


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


def open_bugs_for_source(bugs_list, source_name, series_name):
    lp = get_launchpad()
    ubuntu = get_ubuntu()

    # don't nominate for current series
    if ubuntu.current_series.name == series_name:
        package = ubuntu.getSourcePackage(name=source_name)
    else:
        series = get_series(series_name)
        package = series.getSourcePackage(name=source_name)

    for bug_num in bugs_list:
        try:
            bug = lp.bugs[bug_num]
            bug.addTask(target=package)
            bug.lp_save()
        except (KeyError, lazr.restfulclient.errors.BadRequest, lazr.restfulclient.errors.ServerError):
            # ignore non existing or available bugs
            logging.info("Can't synchronize upstream/downstream bugs for bug #{}. Not blocking on that.".format(bug_num))


def get_available_all_and_ignored_archs(series, ppa=None):
    '''Return a set of available archs, the all arch and finally the archs we can eventually ignored if nothing is published in dest'''
    available_arch = set()
    if ppa and ppa.require_virtualized:
        available_arch = set(VIRTUALIZED_PPA_ARCH)
        arch_all_arch = VIRTUALIZED_PPA_ARCH[0]
    else:
        for arch in series.architectures:
            # HACK: filters armel as it's still seen as available on raring: https://launchpad.net/bugs/1077257
            if arch.architecture_tag == "armel":
                continue
            available_arch.add(arch.architecture_tag)
            if arch.is_nominated_arch_indep:
                arch_all_arch = arch.architecture_tag

    return (available_arch, arch_all_arch, ARCHS_TO_EVENTUALLY_IGNORE)


def get_ppa(ppa_name):
    '''Return a launchpad ppa'''
    ppa_dispatch = ppa_name.split("/")
    return get_launchpad().people[ppa_dispatch[0]].getPPAByName(name=ppa_dispatch[1])

def is_series_current(series_name):
    '''Return if series_name is the edge development version'''
    return get_ubuntu().current_series.name == series_name
