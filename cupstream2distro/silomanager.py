# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
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

import json
import logging
import os
import shutil

from cupstream2distro.settings import SILO_CONFIG_FILENAME, SILO_NAME_LIST, SILO_PREPROD_NAME_LIST, SILO_STATUS_RSYNCDIR
from cupstream2distro.utils import ignored


def get_silo_root_path():
    '''Recursiverly look for a config file as a silo path name from cur dir and return it'''
    silo_root_path = os.path.abspath('.')
    while not os.path.isfile(os.path.join(silo_root_path, SILO_CONFIG_FILENAME)):
        if silo_root_path == os.path.abspath(os.path.dirname(silo_root_path)):
            raise Exception("We are not in a silo config path")
        silo_root_path = os.path.abspath(os.path.dirname(silo_root_path))
    return silo_root_path

def save_config(config, uri=''):
    """Save config in uri and copy to outdir"""
    if not uri:
        uri = get_silo_root_path()

    silo_config_path = os.path.abspath(os.path.join(uri, SILO_CONFIG_FILENAME))
    with ignored(OSError):
        os.makedirs(uri)
    try:
        new_file = "{}.new".format(silo_config_path)
        json.dump(config, open(new_file, 'w'))
        os.rename(new_file, silo_config_path)
    except TypeError as e:
        logging.error("Can't save configuration: " + e.message)
        os.remove(silo_config_path)
        return False
    # copy to outdir
    with ignored(OSError):
        os.makedirs(SILO_STATUS_RSYNCDIR)
    silo_name = os.path.dirname(silo_config_path).split(os.path.sep)[-1]
    dest = os.path.join(SILO_STATUS_RSYNCDIR, silo_name)
    logging.debug("Copying configuration from {} to {}".format(silo_config_path, dest))
    shutil.copy2(silo_config_path, os.path.join(SILO_STATUS_RSYNCDIR, silo_name))
    return True

def load_config(uri=None):
    """return a loaded config

    If no uri, load in the current directory"""
    if not uri:
        uri = os.path.abspath('.')
    logging.debug("Reading configuration in {}".format(uri))
    try:
        return json.load(open(os.path.join(uri, SILO_CONFIG_FILENAME)))
    # if silo isn't configured
    except IOError:
        pass
    except ValueError as e:
        logging.warning("Can't load configuration: " + e.message)
    return None

def remove_status_file(silo_name):
    """Remove status file"""
    os.remove(os.path.join(SILO_STATUS_RSYNCDIR, silo_name))


def is_project_not_in_any_configs(project_name, series, dest, base_silo_uri, ignore_silo, dont_error_but_warn=False):
    """Return true if the project for that serie in that dest is not in any configuration"""
    logging.info("Checking if {} is already configured for {} ({}) in another silo".format(project_name, dest.name, series.name))
    for silo_name in SILO_NAME_LIST:
        # we are reconfiguring current silo, ignoring it
        if ignore_silo == silo_name:
            continue
        config = load_config(os.path.join(base_silo_uri, silo_name))
        if config:
            if (config["global"]["dest"] == dest.self_link and config["global"]["series"] == series.self_link and
                (project_name in config["mps"] or project_name in config["sources"])):
                message = "{} is already prepared for the same serie and destination in {}".format(project_name, silo_name)
                if dont_error_but_warn:
                    logging.warning(message)
                else:
                    logging.error(message)
                return False
    return True


def find_silo_config_for_request_id(request_id, base_silo_uri):
    """Find a config silo matching the request id, return None otherwise"""
    logging.info("Checking if {} is in any assigned silo".format(request_id))
    for silo_name in SILO_NAME_LIST:
        config = load_config(os.path.join(base_silo_uri, silo_name))
        if config:
            if config["requestid"] == request_id:
                return config
    return None


def return_first_available_silo(base_silo_uri, preprod=False):
    """Check which silos are free and return the first available one. We separate preprod and production silos"""
    silo_list = [silo for silo in SILO_NAME_LIST if silo not in SILO_PREPROD_NAME_LIST]
    if preprod:
        silo_list = SILO_PREPROD_NAME_LIST

    for silo_name in silo_list:
        if not os.path.isfile(os.path.join(base_silo_uri, silo_name, SILO_CONFIG_FILENAME)):
            return silo_name
    return None


def get_config_step(config):
    """Get configuration step"""
    return config["global"]["step"]

def set_config_step(config, new_step, uri=''):
    """Set configuration step to new_step"""
    config["global"]["step"] = new_step
    return save_config(config, uri)

def set_config_status(config, status, uri='', add_url=True, ping=True):
    """Change status to reflect latest status"""
    build_url = os.getenv('BUILD_URL')
    url = ""
    if add_url and build_url:
        url = "{}console".format(build_url)
    config["global"]["status"] = {
        "message": status,
        "ping":  ping,
        "url": url
    }
    return save_config(config, uri)

def set_config_pkgversionlist(config, pkglist, uri=''):
    config["global"]["pkgversionlist"] = pkglist
    return save_config(config, uri)

def get_all_projects(config):
    """Get a list of all projets"""
    projects = []
    projects.extend(config["mps"])
    projects.extend(config["sources"])
    return projects
