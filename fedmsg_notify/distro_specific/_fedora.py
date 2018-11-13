# This file is a part of fedmsg-notify.
#
# fedmsg-notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fedmsg-notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fedmsg-notify.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2012, 2013 Red Hat, Inc.
# Authors: Luke Macken <lmacken@redhat.com>

import logging

import dnf
import requests


log = logging.getLogger('moksha.hub')

try:
    import problem
except ImportError:
    log.warn("Could not import the ABRT bindings. You won't be able to see the reported bugs.")
    HAS_ABRT = False
else:
    HAS_ABRT = True


def get_installed_packages():
    """Retrieve the packages installed on the system"""
    base = dnf.Base()
    sack = base.fill_sack(load_system_repo=True)
    query = sack.query()
    installed = query.installed()
    pkgs = installed.run()
    return (pkg.name for pkg in pkgs)

def get_user_packages(usernames):
    packages = set()
    for username in usernames:
        log.info("Querying dist-git for %s's packages" % username)
        response = requests.get(
            "https://src.fedoraproject.org/api/0/user/{}".format(username)
        )
        pkgs = [repo["name"] for repo in response.json()["repos"]]
        log.info("Got %s packages to notify about" % len(pkgs))
        packages.update(pkgs)
    return packages


def get_reported_bugs():
    """
    Get bug numbers from local abrt reports
    """
    if not HAS_ABRT:
        return set()

    bugs = set()

    for prob in problem.list():
        if not hasattr(prob, 'reported_to'):
            continue

        for line in prob.reported_to.splitlines():
            if line.startswith('Bugzilla:'):
                bug_num = int(line.split('=')[-1])
                bugs.add(bug_num)

    return bugs
if not HAS_ABRT:
    get_reported_bugs.disabled = True
