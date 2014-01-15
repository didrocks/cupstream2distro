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

from cupstream2distro.settings import SILO_CONFIG_FILENAME, SILO_NAME_LIST, SILO_STATUS_RSYNCDIR
from cupstream2distro.utils import ignored


def save_config(config, uri=''):
    """Save config in uri and copy to outdir"""
    silo_config_path = os.path.abspath(os.path.join(uri, SILO_CONFIG_FILENAME))
    with ignored(OSError):
        os.makedirs(uri)
    try:
        json.dump(config, open(silo_config_path, 'w'))
    except TypeError as e:
        logging.error("Can't save configuration: " + e.message)
        os.remove(silo_config_path)
        return False
    # copy to outdir
    with ignored(OSError):
        os.makedirs(SILO_STATUS_RSYNCDIR)
    silo_name = os.path.dirname(silo_config_path)
    shutil.copy2(silo_config_path, os.path.join(os.SILO_STATUS_RSYNCDIR, silo_name))
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
    silo_config_path = os.path.abspath('.')
    os.remove(os.path.join(SILO_STATUS_RSYNCDIR, silo_name))


def is_project_not_in_any_configs(project_name, series, dest, base_silo_uri, ignore_silo):
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
                logging.error("{} is already prepared for the same serie and destination in {}".format(project_name, silo_name))
                return False
    return True


def return_first_available_silo(base_silo_uri):
    """Check which silos are free and return the first one"""
    for silo_name in SILO_NAME_LIST:
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

def set_config_status(config, status, uri='', add_url=True):
    """Change status to reflect latest status"""
    build_url = os.getenv('BUILD_URL')
    if add_url and build_url:
        status = "{} ({}console)".format(status , build_url)
    config["global"]["status"] = status
    return save_config(config, uri)

def get_all_projects(config):
    """Get a list of all projets"""
    projects = []
    projects.extend(config["mps"])
    projects.extend(config["sources"])
    return projects
