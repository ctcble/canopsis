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

LOGGING_CONFIGURATION_FILENAME = 'logging.conf'

import logging


class CanopsisLogger(logging.Logger):
    """
    Logger dedicated to Canopsis files.
    """

    pass

logging.setLoggerClass(CanopsisLogger)

# register file configuration changes into the global configuration file
import logging.config


def loggingConfigurationFileObserver(src_path):
    """
    Reuse configuration file in order to parameterize loggers.
    """

    logging.config.fileConfig(src_path)

import cconfiguration
cconfiguration.register_observer(
    LOGGING_CONFIGURATION_FILENAME, loggingConfigurationFileObserver, True)


def getLogger(name=None):
    """
    redirection to logging.getLogger.
    """

    result = logging.getLogger(name)
    return result
