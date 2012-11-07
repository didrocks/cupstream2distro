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

import re
import subprocess

from . import packagemanager


def get_branch(branch_url, dest_dir):
    '''Grab a branch'''
    instance = subprocess.Popen(["bzr", "branch", branch_url, dest_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8")[:-1])  # remove last \n


def get_tip_bzr_revision():
    '''Get latest revision in bzr'''
    instance = subprocess.Popen(["bzr", "log", "-c", "-1", "--line"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8")[:-1])  # remove last \n
    return (int(stdout.split(':')[0]))


def collect_author_bugs(starting_rev, source_package_name):
    '''Collect a dict with authors fixing bugs since last release

    Form: {Author: set(bug_number, )}'''
    author_bugs = _get_all_bugs_in_branch(starting_rev)
    with open("debian/changelog") as f:
        alreadyfixed_bugs = packagemanager.collect_bugs_until_latest_bzr_rev(f, source_package_name)

    # Remove bugs already fixed, discaring author if needed
    authors_to_remove = set()
    for author in author_bugs:
        author_bugs[author] = author_bugs[author] - alreadyfixed_bugs
        if not author_bugs[author]:
            authors_to_remove.add(author)
    for author in authors_to_remove:
        author_bugs.pop(author)
    return author_bugs


def _get_all_bugs_in_branch(starting_rev):
    '''Collect all bugs from the branchs since starting_rev into a dict

    Form: {Author: set(bug_number)}'''
    instance = subprocess.Popen(["bzr", "log", "-r", "{}..".format(starting_rev), "--include-merged", "--forward"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8")[:-1])  # remove last \n

    results = {}
    bug_numbers = set()
    author = None

    # we are trying to match in the commit message:
    # bug #12345, bug#12345, bug12345, bug 12345
    # lp: #12345, lp:#12345, lp:12345, lp: 12345
    # lp #12345, lp#12345, lp12345, lp 12345,
    # https://launchpad.net/bugs/1234567890 and
    # #12345 (but not 12345 for false positive)
    # Support multiple bugs per commit
    bug_regexp = re.compile("((lp:?|bug)[ #]*|#|https://launchpad.net/bugs/)(\d{5,})", re.IGNORECASE)
    author_regexp = re.compile("committer: (.*) <.*>")
    for line in stdout.splitlines():
        matches = bug_regexp.findall(line)
        for match in matches:
            bug_numbers.add(match[-1])
        matches = author_regexp.findall(line)
        for match in matches:
            author = match

        if "---------------------------------" in line:
            if author and bug_numbers:
                results.setdefault(author, set())
                for bug in bug_numbers:
                    results[author].add(bug)
            bug_numbers = set()
            author = None

    # last one
    if author and bug_numbers:
        results.setdefault(author, set())
        for bug in bug_numbers:
            results[author].add(bug)

    return results

