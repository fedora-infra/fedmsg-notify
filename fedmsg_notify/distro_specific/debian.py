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
# Copyright (C) 2013 Nicolas Dandrimont
# Authors: Nicolas Dandrimont <nicolas.dandrimont@crans.org>

from collections import defaultdict
from cStringIO import StringIO
import email.utils
import gzip
import logging
import urllib2

import deb822


UPLOADERS = defaultdict(set)
log = logging.getLogger('moksha.hub')


def _populate_uploaders():
    """Populate the uploaders dict with uploaders"""
    UPLOADERS_URI = "http://http.debian.net/debian/indices/Uploaders.gz"

    f = urllib2.urlopen(UPLOADERS_URI)

    if f.getcode() != 200:
        log.warn("Could not retrieve uploaders URI: error %s" % f.getcode())
        return

    gzip_file = gzip.GzipFile(fileobj=StringIO(f.read()))

    UPLOADERS.clear()

    for line in gzip_file.readlines():
        try:
            package, uploader = line.strip().split(None, 1)
        except ValueError:
            continue

        uploader_name, uploader_email = email.utils.parseaddr(uploader)
        try:
            uploader_localpart, uploader_domain = uploader_email.split("@")
        except ValueError:
            uploader_domain = ""

        UPLOADERS[uploader].add(package)
        UPLOADERS[uploader_email].add(package)
        if uploader_name:
            UPLOADERS[uploader_name].add(package)
        if uploader_domain == "debian.org":
            UPLOADERS[uploader_localpart].add(package)


def get_installed_packages():
    """Retrieve the packages installed on the system"""
    STATE_FILE = "/var/lib/apt/extended_states"
    with open(STATE_FILE) as f:
        installed_packages = deb822.Deb822.iter_paragraphs(f)
        for package in installed_packages:
            if "Auto-Installed" in package and package["Auto-Installed"] == 1:
                continue
            yield package["Package"]


def get_user_packages(usernames):
    """
    Retrieve the packages maintained by people matching one of the `usernames`.

    We retrieve an Uploaders indice from a mirror and cache it.
    """
    if not UPLOADERS:
        _populate_uploaders()

    packages = set()
    for username in usernames:
        packages |= UPLOADERS[username]

    return packages


def get_reported_bugs():
    """
    Not implemented on debian, just return empty set
    """

    return set()
