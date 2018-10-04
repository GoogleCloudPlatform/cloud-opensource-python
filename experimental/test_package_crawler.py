import ast
import os
import unittest

from package_crawler_static import get_package_info, get_module_info


class TestSimplePackages(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()

    def test_simple_function(self):
        expected = {
            'modules': {
                'simple_function': {
                    'classes': {},
                    'functions': {
                        'hello': {
                            'args': []
                        }
                    }
                },
            },
            'subpackages': {}
        }
        location = os.path.join(self.cwd, 'test_packages/simple_function')
        info = get_package_info(location)
        self.assertEqual(expected, info)

