#!/usr/bin/env python
#--------------------------------
# Copyright (c) 2014 "Capensis" [http://www.capensis.com]
#
# This file is part of Canopsis.
#
# Canopsis is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canopsis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import os.path

CONFIGURATION_DIRECTORY = '~/etc/'


class _ConfigurationFileSystemEventHandler(FileSystemEventHandler):

    def __init__(self):
        self.configurationObservers = dict()
        super(_ConfigurationFileSystemEventHandler, self).__init__()

    def register_observer(self, configuration_file, observer, call=False):
        self.configurationObservers[configuration_file] = observer
        if call:
            src_path = os.path.join(
                CONFIGURATION_DIRECTORY, configuration_file)
            observer(src_path)

    def _callObserver(self, event):
        filename = os.path.basename(event.src_path)
        observer = self.configurationObservers.get(filename, None)
        if observer is not None:
            observer(event.src_path)

    def on_modified(self, event):
        self._callObserver(event)

    def on_created(self, event):
        self._callObserver(event)

_file_handler = _ConfigurationFileSystemEventHandler()
_observer = Observer()
_observer.schedule(
    _file_handler, path=CONFIGURATION_DIRECTORY, recursive=False)
_observer.start()

import gevent
import signal


def stop_observer():
    _observer.stop()
    _observer.join()

gevent.signal(signal.SIGTERM, stop_observer)
gevent.signal(signal.SIGINT, stop_observer)


def register_observer(configuration_file, observer, call=False):
    _file_handler.register_observer(configuration_file, observer, call)
