# Copyright (C) 2021-2022 Horus View and Explore B.V.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pyinfra import host
from pyinfra.api import OperationError

from horus_deploy.operations import system

METADATA = {
    "name": "timedate",
    "description": "Set the date, time, time zone, and enable/disable NTP.",
    "parameters": {
        "dt": (
            "Set date and/or time. The date format is YYYY-MM-DD and the "
            "time format is HH:MM:SS. To set the date/time NTP must be "
            "disabled."
        ),
        "ntp": "Enable or disable NTP (automatic time synchronization).",
        "tz": "An IANA time zone identifier, e.g. Europe/Amsterdam.",
    },
}

if not (host.data.dt or host.data.ntp or host.data.tz):
    raise OperationError("no parameters given")
if host.data.ntp:
    system.set_ntp(host.data.ntp == "True")
if host.data.dt:
    system.set_time(host.data.dt)
if host.data.tz:
    system.set_time_zone(host.data.tz)
