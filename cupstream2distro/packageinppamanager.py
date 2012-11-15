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

import logging
import os
import re

from .packageinppa import PackageInPPA


def _ensure_removed_from_set(target_set, content_to_remove):
    '''Silent removal from an existing set'''
    try:
        target_set.remove(content_to_remove)
    except KeyError:
        pass  # in case we missed the "build" step


def get_all_packages_uploaded():
    '''Get (package, version) of all packages uploaded'''

    result = set()
    source_package_regexp = re.compile("(.*)_(.*)_source.changes")
    for file in os.listdir('.'):
        substract = source_package_regexp.findall(file)
        if substract:
            result.add(substract[0])
    return result


def update_all_packages_status(packages_not_in_ppa, packages_building, packages_failed, only_arch_all=False):
    '''Update all packages status, checking in the ppa'''

    for current_package in (packages_not_in_ppa.union(packages_building)):
        logging.info("current_package: " + current_package.source_name + " " + current_package.version)
        package_status = current_package.get_status(only_arch_all)
        if package_status != None:  # global package_status can be 0 (building), 1 (failed), 2 (published)
            # if one arch building, still considered as building
            if package_status == PackageInPPA.BUILDING:
                _ensure_removed_from_set(packages_not_in_ppa, current_package)  # maybe already removed
                packages_building.add(current_package)
            # if one arch failed, considered as failed
            elif package_status == PackageInPPA.FAILED:
                _ensure_removed_from_set(packages_building, current_package)  # in case we missed the "build" step
                _ensure_removed_from_set(packages_not_in_ppa, current_package)  # in case we missed the "wait" step
                packages_failed.add(current_package)
            elif package_status == PackageInPPA.PUBLISHED:
                _ensure_removed_from_set(packages_building, current_package)  # in case we missed the "build" step
                _ensure_removed_from_set(packages_not_in_ppa, current_package)  # in case we missed the "wait" step