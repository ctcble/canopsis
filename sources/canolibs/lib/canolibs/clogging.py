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

# file for canopsis logging configuration file
LOGGING_CONFIGURATION_FILENAME = 'logging.conf'
# file for python logging configuration file
PYTHON_LOGGING_CONFIGURATION_FILENAME = 'python-logging.conf'


import os.path

LOG_DIRECTORY = os.path.expanduser('~/var/log/')

INFO_FORMAT = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"

DEBUG_FORMAT = "%(asctime)s [%(name)s] [%(levelname)s] [path: %(pathname)s] [p: %(process)d] [t: %(thread)d] [f: %(funcName)s] [l: %(lineno)d] %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

import logging

INFO_FORMATTER = logging.Formatter(fmt=INFO_FORMAT, datefmt=DATE_FORMAT)
DEBUG_FORMATTER = logging.Formatter(fmt=DEBUG_FORMAT, datefmt=DATE_FORMAT)


class CanopsisLogger(logging.Logger):
    """
    Logger dedicated to Canopsis files.
    """

    def __init__(self, name, level=logging.INFO):
        """
        Create a default file handler where filename corresponds to input name.
        Name tree is preserved in log file tree.
        """

        super(CanopsisLogger, self).__init__(name, level)

        filename = name.replace('.', os.path.sep) + '.log'
        path = os.path.join(LOG_DIRECTORY, filename)
        if not os.path.exists(path):
            directory = os.path.dirname(path)
            if not os.path.exists(directory):
                os.makedirs(directory)

        self.handler = logging.FileHandler(path, 'a')
        self.addHandler()

    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """
        Change dynamically of formatter if no new handler has been requested.
        """

        if self.handler is not None:
            if self.isEnabledFor(level):
                if level <= logging.DEBUG:
                    self.handler.setFormatter(DEBUG_FORMATTER)
                else:
                    self.handler.setFormatter(INFO_FORMATTER)

        super(CanopsisLogger, self).log(level, msg, *args, **kwargs)

        # log debug message for this
        if self is not _logger:
            _logger.debug('log:%s, level: %s, msg: %s', self.name, level, msg)

    def addHandler(self, handler=None):
        """
        Check if the call has been done during self initialization.
        """

        if handler is None:
            handler = self.handler
        else:
            self.handler = None

        super(CanopsisLogger, self).addHandler(handler)

logging.setLoggerClass(CanopsisLogger)

import inspect


def getLogger(name=None):
    """
    Get a logger related to callee module.
    """

    if name is None:
        f_back = inspect.currentframe().f_back
        # get previous frame module name
        name = f_back.f_globals['__name__']
        if name == '__main__':
            # get filename in case of main process
            name = f_back.f_code.co_filename
            if name.endswith('.py'):
                name = name[:-3]

    result = logging.getLogger(name)
    return result

# instantiate a logger
_logger = getLogger()


def getRootLogger():
    """
    Get Root logger.
    """

    result = logging.getLogger()
    return result

# bind observers to both configuration files

# register file configuration changes into the global configuration file
import ConfigParser
LEVEL = 'level'


def _loggingConfigurationFileObserver(src_path):
    """
    Reuse simple configuration file in order to parameterize loggers.
    """

    _logger.debug('src_path: %s', src_path)

    config_parser = ConfigParser.RawConfigParser()
    config_parser.read(src_path)

    for section in config_parser.sections:
        logger = logging.getLogger(section)

        if config_parser.has_option(section, LEVEL):
            level = config_parser.get(section, LEVEL, None)

            if str.isdigit(level):
                level = int(level)

            logger.setLevel(level)

    logging.config.fileConfig(src_path)

import cconfiguration

# hack for adding a logger in cconfiguration
cconfiguration._logger = getLogger('cconfiguration')

cconfiguration.register_observer(
    LOGGING_CONFIGURATION_FILENAME,
    _loggingConfigurationFileObserver, True)

import logging.config


def _pythonLoggingConfigurationFileObserver(src_path):
    """
    Reuse python logging configuration file in order to parameterize loggers.
    """

    _logger.debug('src_path: %s', src_path)

    logging.config.fileConfig(src_path)

cconfiguration.register_observer(
    PYTHON_LOGGING_CONFIGURATION_FILENAME,
    _pythonLoggingConfigurationFileObserver, True)
