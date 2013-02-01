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
# Copyright (C) 2012 Red Hat, Inc.
# Authors: Luke Macken <lmacken@redhat.com>

import os
import yum
import json
import logging

from twisted.internet import reactor
from fedora.client.pkgdb import PackageDB

log = logging.getLogger('moksha.hub')


class Filter(object):
    __description__ = None
    __user_entry__ = None

    def __init__(self, settings):
        self.settings = settings

    def match(self, msg, processor):
        raise NotImplementedError

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


class ReportedBugsFilter(Filter):
    """ Matches messages that reference bugs that abrt has encountered """
    __description__ = 'Bugs that you have encountered'

    def __init__(self, settings):
        """ Pull bug numbers out of local abrt reports """
        self.bugs = set()
        crash_dir = os.path.expanduser('~/.cache/abrt/spool')
        for crash in os.listdir(crash_dir):
            report = os.path.join(crash_dir, crash, 'reported_to')
            if os.path.exists(report):
                for line in open(report):
                    if line.startswith('Bugzilla:'):
                        #bug_url = line.split('URL=')[-1]
                        bug_num = int(line.split('=')[-1])
                        self.bugs.add(bug_num)

    def match(self, msg, processor):
        """ Check if this update fixes and of our bugs """
        if processor.__name__ == 'Bodhi':
            update = msg['msg'].get('update')
            if update:
                bugs = [bug['bz_id'] for bug in update['bugs']]
                for bug in self.bugs:
                    if bug in bugs:
                        log.info("Message contains bug that user filed!")
                        return True


class MyPackageFilter(Filter):
    """ Matches messages regarding packages that a given user has ACLs on """
    __description__ = 'Packages that these users maintain'
    __user_entry__ = 'Usernames'

    def __init__(self, settings):
        self.usernames = settings.replace(',', ' ').split()
        self.packages = set()
        def _query_pkgdb():
            for username in self.usernames:
                log.info("Querying the PackageDB for %s's packages" % username)
                for pkg in PackageDB().user_packages(username)['pkgs']:
                    self.packages.add(pkg['name'])
        reactor.callInThread(_query_pkgdb)

    def match(self, msg, processor):
        packages = processor.packages(msg)
        for package in self.packages:
            if package in packages:
                return True


class UsernameFilter(Filter):
    """ Matches messages that contain specific usernames """
    __description__ = 'Messages that reference specific users'
    __user_entry__ = 'Usernames'

    def __init__(self, settings):
        self.usernames = settings.replace(',', ' ').split()

    def match(self, msg, processor):
        for username in processor.usernames(msg):
            if username in self.usernames:
                return True


class PackageFilter(Filter):
    """ Matches messages referencing packages that are specified by the user """
    __description__ = 'Messages that reference specific packages'
    __user_entry__ = 'Packages'

    def __init__(self, settings):
        self.packages = settings.replace(',', ' ').split()

    def match(self, msg, processor):
        for package in processor.packages(msg):
            if package in self.packages:
                return True


class InstalledPackageFilter(Filter):
    """ Matches messages referencing packages that are installed locally """
    __description__ = 'Packages that you have installed'

    def __init__(self, settings):
        self.packages = []
        def _query_yum():
            yb = yum.YumBase()
            yb.doConfigSetup(init_plugins=False)
            self.packages = [pkg.base_package_name for pkg in
                            yb.doPackageLists(pkgnarrow='installed')]
        reactor.callInThread(_query_yum)

    def match(self, msg, processor):
        for package in processor.packages(msg):
            if package in self.packages:
                return True


def get_enabled_filters(settings, key='enabled-filters'):
    try:
        return json.loads(settings.get_string(key))
    except ValueError:
        return settings.get_string(key).split()


filters = [
    ReportedBugsFilter,
    InstalledPackageFilter,
    PackageFilter,
    MyPackageFilter,
    UsernameFilter,
]
