"""Unit tests for argus.logging_service."""

import logging
import unittest

from argus.configuration import Configuration
from argus.logging_service import get_logger, initialize_logging


class LoggingServiceTests(unittest.TestCase):
    def test_initialize_logging_sets_level_from_configuration(self):
        configuration = Configuration({"logging": {"level": "DEBUG"}})

        logger = initialize_logging(configuration)

        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(logger.name, "argus")

    def test_initialize_logging_defaults_to_info_when_unset(self):
        configuration = Configuration({})

        logger = initialize_logging(configuration)

        self.assertEqual(logger.level, logging.INFO)

    def test_initialize_logging_does_not_duplicate_handlers(self):
        configuration = Configuration({"logging": {"level": "INFO"}})

        initialize_logging(configuration)
        handler_count_after_first_call = len(logging.getLogger("argus").handlers)
        initialize_logging(configuration)
        handler_count_after_second_call = len(logging.getLogger("argus").handlers)

        self.assertEqual(handler_count_after_first_call, handler_count_after_second_call)

    def test_get_logger_returns_namespaced_child_logger(self):
        logger = get_logger("bootstrap")

        self.assertEqual(logger.name, "argus.bootstrap")

    def test_get_logger_without_name_returns_root_argus_logger(self):
        logger = get_logger()

        self.assertEqual(logger.name, "argus")


if __name__ == "__main__":
    unittest.main()
