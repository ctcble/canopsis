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
from ConfigParser import RawConfigParser

CONFIGURATION_DIRECTORY = os.path.expanduser('~/etc/')
CONFIGURATION_FILE = 'configuration.conf'

MANUAL_RECONFIGURATION = 'manual_reconfiguration'

GLOBAL = 'GLOBAL'
_logger = None


class _ConfigurationFileSystemEventHandler(FileSystemEventHandler):
    """
    File system handler which listen modification of configuration directory content
    and notifies configuration file bound observers.
    """

    def __init__(self):

        super(_ConfigurationFileSystemEventHandler, self).__init__()

        self.manual_configuration = True
        self.configurationObservers = dict()
        self.config_parser = RawConfigParser()
        self.register_observer(
            CONFIGURATION_FILE, self._check_configuration)

    def _check_configuration(self, src_path):
        """
        Observer method.
        """

        _logger.debug('src_path: %s', src_path)

        self.config_parser.read(src_path)

        manual_configuration = \
            self.config_parser.getboolean(GLOBAL, MANUAL_RECONFIGURATION)
        if not manual_configuration and self.manual_configuration:
            self.manual_configuration = False
            self.callObservers()
        self.manual_configuration = manual_configuration

    def callObservers(self):
        """
        Call all observers.
        """

        _logger.debug('')

        for configuration_file, observer in \
                self.configurationObservers.iteritems():
            src_path = os.path.join(
                CONFIGURATION_DIRECTORY, configuration_file)
            self._callObserver(src_path)

    def register_observer(self, configuration_file, observer, call=False):
        """
        Register an observer bound to input configuration_file.
        If call is True, the observer is called just after registering.
        """

        self.configurationObservers[configuration_file] = observer

        if call:
            src_path = os.path.join(
                CONFIGURATION_DIRECTORY, configuration_file)
            self._callObserver(src_path)

    def _callObserver(self, src_path):
        """
        Call observer bound to event src_path.
        """

        _logger.debug('src_path: %s', src_path)

        src_path = os.path.expanduser(src_path)

        if not self.manual_configuration:
            filename = os.path.basename(src_path)
            observer = self.configurationObservers.get(filename, None)
            if observer is not None:
                observer(src_path)

    def on_modified(self, event):
        """
        Call when a configuration file is modified.
        """

        _logger.debug('event: %s', event)

        self._callObserver(event.src_path)

    def on_created(self, event):
        """
        Call when a configuration file is created.
        """

        _logger.debug('event: ', event)

        self._callObserver(event.src_path)


def register_observer(configuration_file, observer, call=False):
    """
    Shortcut method which register an observer and bound it with input configuration_file.
    If call is True (False by default), the observer is called just after being registered.
    """

    _logger.debug(
        'configuration_file: %s, observer: %s, call: %s',
        configuration_file, observer, call)

    _file_system_event_handler.register_observer(
        configuration_file, observer, call)

# singleton for configuration file system event handler
_file_system_event_handler = _ConfigurationFileSystemEventHandler()
# watchdog observer which register the singleton _file_system_event_handler in configuration directory content modification observers.
_observer = Observer()

_observer.schedule(
    _file_system_event_handler, path=CONFIGURATION_DIRECTORY, recursive=False)
_observer.start()

import atexit


@atexit.register
def _stop_observer():
    """
    Stop listening of configuration file event handler on configuration directory.
    """
    if _logger is not None:
        _logger.debug('')

    _observer.stop()
    _observer.join()
