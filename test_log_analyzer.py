#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import random
import log_analyzer
import os

class TestLogAnalyzer(unittest.TestCase):
    def setUp(self):
        self.tmp_conf_file = '/var/tmp/test'+ str(random.randint(1,999))
        self.tmp_conf_file_str = "[GLOBAL]\nREPORT_SIZE: 333\nREPORT_DIR: ./reports\n" \
                                 "LOG_DIR: ./log\nTS_FILE: /var/tmp/log_analyzer.ts"
        with open(self.tmp_conf_file,'wt') as f:
            f.write(self.tmp_conf_file_str)

    def test_read_config(self):
        log_analyzer.read_config(self.tmp_conf_file)
        self.assertEqual(333, log_analyzer.config["REPORT_SIZE"])
        self.assertEqual('./log', log_analyzer.config["LOG_DIR"])
        self.assertEqual('./reports', log_analyzer.config["REPORT_DIR"])

    def test_kkk(self):
        pass

    def tearDown(self):
        os.remove(self.tmp_conf_file)



