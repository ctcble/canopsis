import logging
import logging.config
import cconfiguration

LOGGING_CONFIGURATION_FILENAME = 'logging.conf'


def openLoggingConfigurationFile(src_path):
    logging.config.fileConfig(src_path)


class CanopsisLogger(logging.Logger):
    """
    Logger dedicated to Canopsis files.
    """

    pass

logging.setLoggerClass(CanopsisLogger)

# register file configuration changes into the global configuration file
cconfiguration.register_observer(
    LOGGING_CONFIGURATION_FILENAME, openLoggingConfigurationFile, True)
