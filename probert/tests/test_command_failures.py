import asyncio
import logging
import subprocess
import unittest
from unittest import mock

from probert import bcache, lvm, mount, utils
from probert.tests.test_utils import create_script


class TestRunContractUnchanged(unittest.TestCase):

    def test_run_returns_stdout_or_none(self):
        with create_script('#!/bin/sh\necho hi\n') as script:
            self.assertEqual('hi\n', utils.run([script]))
        with create_script('#!/bin/sh\nexit 3\n') as script:
            with self.assertLogs('probert.utils', level=logging.WARNING):
                self.assertIsNone(utils.run([script]))

    def test_arun_returns_stdout_or_none(self):
        with create_script('#!/bin/sh\necho oops >&2\nexit 4\n') as script:
            with self.assertLogs('probert.utils', level=logging.WARNING) as m:
                self.assertIsNone(asyncio.run(utils.arun([script])))
        self.assertIn('oops', m.output[-1])

    def test_failure_is_logged_at_warning_with_stderr(self):
        with create_script('#!/bin/sh\necho bad-thing >&2\nexit 1\n') as s:
            with self.assertLogs('probert.utils', level=logging.WARNING) as m:
                utils.run([s])
        self.assertEqual(1, len(m.output))
        self.assertTrue(m.output[0].startswith('WARNING:probert.utils:'))
        self.assertIn('bad-thing', m.output[0])


class TestProbeStderrIsKept(unittest.TestCase):

    def _failure(self):
        return subprocess.CalledProcessError(
            2, ['cmd'], stderr=b'device busy\n')

    def test_findmnt_failure_logs_stderr(self):
        with mock.patch('probert.mount.subprocess.run',
                        side_effect=self._failure()) as m_run:
            with self.assertLogs('probert.utils', level='WARNING') as logs:
                self.assertEqual({}, mount.findmnt())
        self.assertEqual(subprocess.PIPE, m_run.call_args.kwargs['stderr'])
        self.assertIn('device busy', logs.output[0])

    def test_lvm_probe_failure_logs_stderr(self):
        with mock.patch('probert.lvm.subprocess.run',
                        side_effect=self._failure()) as m_run:
            with self.assertLogs('probert.utils', level='WARNING') as logs:
                lvm.probe_lvs_report()
        self.assertEqual(subprocess.PIPE, m_run.call_args.kwargs['stderr'])
        self.assertIn('device busy', logs.output[0])

    def test_bcache_failure_is_not_silent(self):
        cp = subprocess.CompletedProcess(
            ['bcache-super-show'], 1, stdout=b'', stderr=b'not a bcache\n')
        with mock.patch('probert.bcache.subprocess.run', return_value=cp):
            with self.assertLogs('probert.utils', level='WARNING') as logs:
                self.assertEqual({}, bcache.superblock_asdict('/dev/sda1'))
        self.assertIn('not a bcache', logs.output[0])
