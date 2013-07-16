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


class PackageInPPA():

    (BUILDING, FAILED, PUBLISHED) = range(3)

    def __init__(self, source_name, version, ppa, destarchive, series,
                 available_archs_in_ppa, arch_all_arch, archs_to_eventually_ignore):
        self.source_name = source_name
        self.version = version
        self.series = series
        self.arch_all_arch = arch_all_arch
        self.ppa = ppa
        self.current_status = {}

        # Get archs we should look at
        version_for_source_file = version.split(':')[-1]
        dsc_filename = "{}_{}.dsc".format(source_name, version_for_source_file)
        regexp = re.compile("^Architecture: (.*)\n")
        for line in open(dsc_filename):
            arch_lists = regexp.findall(line)
            if arch_lists:
                arch_lists = arch_lists[0]
                if "any" in arch_lists:
                    self.archs = available_archs_in_ppa.copy()
                elif arch_lists == "all":
                    self.archs = set([self.arch_all_arch])
                else:
                    archs_supported_by_package = set()
                    for arch in arch_lists.split():
                        archs_supported_by_package.add(arch)
                    self.archs = archs_supported_by_package.intersection(available_archs_in_ppa)
                break
        # ignore some eventual archs if doesn't exist in latest published version in dest
        if archs_to_eventually_ignore:
            try:
                previous_source = destarchive.getPublishedSources(exact_match=True, source_name=self.source_name,
                                                                  distro_series=self.series, status="Published")[0]
                for binary in previous_source.getPublishedBinaries():
                    if binary.architecture_specific and binary.distro_arch_series.architecture_tag in archs_to_eventually_ignore:
                        archs_to_eventually_ignore -= set([binary.distro_arch_series.architecture_tag])
                    if not archs_to_eventually_ignore:
                        break

            except IndexError:
                # no package in dest, don't wait on any archs_to_eventually_ignore
                pass
            # remove from the inspection remaining archs to ignore
            if archs_to_eventually_ignore:
                self.archs -= archs_to_eventually_ignore


    def get_status(self, only_arch_all):
        '''Look at the package status in the ppa'''

        self._refresh_status()
        if not self.current_status:
            return None

        current_package_building = False
        current_package_failed = False
        for arch in self.current_status:
            if only_arch_all and arch != self.arch_all_arch:
                continue
            str_status = "published"
            if self.current_status[arch] == PackageInPPA.BUILDING:
                current_package_building = True
                str_status = "building"
            if self.current_status[arch] == PackageInPPA.FAILED:
                current_package_failed = True
                str_status = "failed"
            logging.info("arch: {}, status: {}".format(arch, str_status))

        if current_package_building:
            return self.BUILDING
        # no more package is building, if one failed, time to signal it
        if current_package_failed:
            return self.FAILED
        # if it's not None, not BUILDING, nor FAILED, it's PUBLISHED
        return self.PUBLISHED

    def _refresh_archs_skipped(self):
        '''Refresh archs that we should skip for this build'''

        for arch in self.archs.copy():
            if os.path.isfile("{}.{}.ignore".format(self.source_name, arch)):
                logging.warning("Request to ignore {} on {}.".format(self.source_name, arch))
                try:
                    self.archs.remove(arch)
                except ValueError:
                    logging.warning("Request to ignore {} on {} has been proceeded, but this one wasn't in the list we were monitor for.".format(self.source_name, arch))
                try:
                    self.current_status.pop(arch)
                except KeyError:
                    pass

    def _refresh_status(self):
        '''Refresh status from the ppa'''

        self._refresh_archs_skipped()

        # first step, get the source published
        if not self.current_status:
            (self.current_status, self.source) = self._get_status_for_source_package_in_ppa()
        # check the binary status
        if self.current_status:
            self.current_status = self._get_status_for_binary_packages_in_ppa()

    def _get_status_for_source_package_in_ppa(self):
        '''Return current_status for source package in ppa.

        The status is dict (if not None) with {arch: status} and can be:
            - None -> not visible yet
            - BUILDING -> currently Building (or waiting to build)
            - FAILED -> Build failed for this arch or has been canceled
            - PUBLISHED -> All packages (including arch:all from other archs) published.

            Only the 2 first status are returned by this call. See _get_status_for_binary_packages_in_ppa
            for the others.'''

        try:
            source = self.ppa.getPublishedSources(exact_match=True, source_name=self.source_name, version=self.version, distro_series=self.series)[0]
            logging.info("Source available in ppa")
            current_status = {}
            for arch in self.archs:
                current_status[arch] = self.BUILDING
            return (current_status, source)
        except (KeyError, IndexError):
            return ({}, None)

    def _get_status_for_binary_packages_in_ppa(self):
        '''Return current status for package in ppa

        The status is dict (if not None) with {arch: status} and can be:
            - None -> not visible yet
            - BUILDING -> currently Building (or waiting to build)
            - FAILED -> Build failed for this arch or has been canceled
            - PUBLISHED -> All packages (including arch:all from other archs) published.

            Only the 3 last statuses are returned by this call. See _get_status_for_source_package_in_ppa
            for the other.'''

        # Try to see if all binaries availables for this arch are built, including arch:all on other archs
        status = self.current_status
        at_least_one_published_binary = False
        for binary in self.source.getPublishedBinaries():
            at_least_one_published_binary = True
            # all binaries for an arch are published at the same time
            # launchpad is lying, it's telling that archs not in the ppa are built (for arch:all). Even for non supported arch!
            # for instance, we can have the case of self.arch_all_arch (arch:all), built before the others and amd64 will be built for it
            if binary.status == "Published" and (binary.distro_arch_series.architecture_tag == self.arch_all_arch or
               (binary.distro_arch_series.architecture_tag != self.arch_all_arch and binary.architecture_specific)):
                status[binary.distro_arch_series.architecture_tag] = self.PUBLISHED

        # Looking for builds on archs still BUILDING (just loop on builds once to avoid too many lp requests)
        needs_checking_build = False
        build_state_failed = ('Failed to build', 'Chroot problem', 'Failed to upload', 'Cancelled build', 'Build for superseded Source')
        for arch in self.archs:
            if self.current_status[arch] == self.BUILDING:
                needs_checking_build = True
        if needs_checking_build:
            for build in self.source.getBuilds():
                # ignored archs
                if not build.arch_tag in self.current_status:
                    continue
                if self.current_status[build.arch_tag] == self.BUILDING:
                    if build.buildstate in build_state_failed:
                        logging.error("{}: Build {} ({}) failed because of {}".format(build.arch_tag, build.title,
                                                                                       build.web_link, build.buildstate))
                        status[build.arch_tag] = self.FAILED
                    # Another launchpad trick: if a binary arch was published, but then is superseeded, getPublishedBinaries() won't list
                    # those binaries anymore. So it's seen as BUILDING again.
                    # If there is a successful build record of it and the source is superseded, it means that it built fine at some point,
                    # Another arch will fail as superseeded.
                    # We don't just retain the old state of "PUBLISHED" because maybe we started the script with that situation already
                    elif build.buildstate not in build_state_failed and self.source.status == "Superseded":
                        status[build.arch_tag] = self.PUBLISHED

        # There is no way to know if there are some arch:all packages (and there are not in publishedBinaries for this arch until
        # it's built on arch_all_arch). So mark all arch to BUILDING if self.arch_all_arch is building or FAILED if it failed.
        if self.arch_all_arch in status and status[self.arch_all_arch] != self.PUBLISHED:
            for arch in self.archs:
                if status[arch] == self.PUBLISHED:
                    status[arch] = status[self.arch_all_arch]
                    if arch != self.arch_all_arch and status[arch] == self.FAILED:
                        logging.error("{} marked as FAILED because {} build FAILED and we may miss arch:all packages".format(arch, self.arch_all_arch))

        return status
