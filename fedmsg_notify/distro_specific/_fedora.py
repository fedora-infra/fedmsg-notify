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

import yum
import problem
import pkgdb2client


log = logging.getLogger('moksha.hub')


def get_installed_packages():
    """Retrieve the packages installed on the system"""
    yb = yum.YumBase()
    yb.doConfigSetup(init_plugins=False)
    for pkg in yb.doPackageLists(pkgnarrow='installed'):
        yield pkg.base_package_name


def get_user_packages(usernames):
    packages = set()
    for username in usernames:
        log.info("Querying the PackageDB for %s's packages" % username)
        pkgs = pkgdb2client.PkgDB().get_packager_package(username)
        for category in ('point of contact', 'co-maintained', 'watch'):
            for pkg in pkgs[category]:
                packages.add(pkg['name'])
    return packages


def get_reported_bugs():
    """
    Get bug numbers from local abrt reports
    """

    bugs = set()

    for prob in problem.list():
        if not hasattr(prob, 'reported_to'):
            continue

        for line in prob.reported_to.splitlines():
            if line.startswith('Bugzilla:'):
                bug_num = int(line.split('=')[-1])
                bugs.add(bug_num)

    return bugs
