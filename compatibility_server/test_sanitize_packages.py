# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from compatibility_checker_server import _sanitize_packages
import configs
import logging
import pip_checker
import unittest


class Test__sanitize_packages(unittest.TestCase):

    def test__sanitize_packages(self):
        packages = configs.WHITELIST_PKGS
        res = _sanitize_packages(packages)
        self.assertEqual(res, packages)

        urls = [url for url in configs.WHITELIST_URLS.keys()]
        res = _sanitize_packages(urls)
        self.assertEqual(res, urls)

    @unittest.skip("local testing only")
    def test_all_whitelists_pip_install(self):
        py2_pkgs, py3_pkgs = [], []
        for pkg in configs.WHITELIST_PKGS:
            if pkg not in configs.PKG_PY_VERSION_NOT_SUPPORTED[2]:
                py2_pkgs.append(pkg)
            if pkg not in configs.PKG_PY_VERSION_NOT_SUPPORTED[3]:
                py3_pkgs.append(pkg)

        for url, pkg in configs.WHITELIST_URLS.items():
            if pkg not in configs.PKG_PY_VERSION_NOT_SUPPORTED[2]:
                py2_pkgs.append(url)
            if pkg not in configs.PKG_PY_VERSION_NOT_SUPPORTED[3]:
                py3_pkgs.append(url)

        args = [
            # ('python', py2_pkgs),
            ('python3', py3_pkgs),
        ]
        for command, packages in args:
            pip_result = pip_checker.check([command, '-m', 'pip'],
                                           packages,
                                           clean=True)
            self.assertIsNotNone(pip_result)

            results = dict(
                result=pip_result.result_type.name,
                packages=pip_result.packages,
                description=pip_result.result_text,
                dependency_info=pip_result.dependency_info)
            if results['result'] == 'INSTALL_ERROR':
                logging.warning(command)
                logging.warning(results['description'])
            self.assertFalse(results['result'] == 'INSTALL_ERROR')

    def test_nonwhitelisted_packages(self):
        packages = [
            'requests',
            'Scrapy',
            'wxPython',
            'Pillow',
            'numpy',
            'Pygame',
        ]
        res = _sanitize_packages(packages)
        self.assertEqual(res, [])
