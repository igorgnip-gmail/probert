import unittest
from unittest import mock

from probert import zfs


class TestZfsGetProperties(unittest.TestCase):
    @mock.patch('probert.zfs.subprocess.run')
    def test_zfs_get_properties_ok(self, m_run):
        output = '''\
tank\ttype\tfilesystem\t-'
tank\tused\t118272\t-
tank\tquota\t0\tdefault
'''
        m_run.return_value.stdout = output.encode('utf-8')
        result = zfs.zfs_get_properties('tank')
        self.assertIn('tank', result)
        self.assertEqual(
                '118272',
                result['tank']['properties']['used']['value'])
        self.assertEqual('0', result['tank']['properties']['quota']['value'])
        self.assertEqual(
                'default',
                result['tank']['properties']['quota']['source'])
