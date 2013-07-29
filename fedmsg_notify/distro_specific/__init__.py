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

import logging


log = logging.getLogger('moksha.hub')

try:
    from .debian import *
except ImportError:
    pass

try:
    from .fedora import *
except ImportError:
    pass

try:
    get_installed_packages
except NameError:
    log.warn("Could not import distro-specific packages. Stubbing out the package management functions.")
    def get_installed_packages():
        """Retrieve the packages installed on the system"""
        return []

try:
    get_user_packages
except NameError:
    log.warn("Could not import distro-specific packages. Stubbing out the package management functions.")
    def get_user_packages(usernames):
        """Retrieve the packages maintained by `usernames`"""
        return []
