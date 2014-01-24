import unittest
import clogging
import os

LOGGER_NAME = 'LOGGER_NAME'


class LoggingTest(unittest.TestCase):

    def setUp(self):
        pass

    def testLogger(self):
        logger = clogging.getLogger('plop')
        logger.debug()
        pass

if __name__ == '__main__':
    unittest.main()
