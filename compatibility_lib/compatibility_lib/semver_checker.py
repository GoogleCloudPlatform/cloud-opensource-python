# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""checks two packages for semver breakage"""

from compatibility_lib import package_crawler_static as crawler


# TODO: This needs more sophisticated logic
# - needs to look at args
def check(old_dir, new_dir):
    """checks for semver breakage for two local directories
    it looks at all the attributes found by get_package_info
    (module, class, function names) for old_dir and making sure they are also
    in new_dir in a BFS

    Args:
        old_dir: directory containing old files
        new_dir: directory containing new files

    Returns:
        False if changes breaks semver, True if semver is preserved
    """
    old_pkg_info = crawler.get_package_info(old_dir)
    new_pkg_info = crawler.get_package_info(new_dir)

    unseen = [(old_pkg_info, new_pkg_info)]
    i = 0
    while i < len(unseen):
        old, new = unseen[i]
        for key in old.keys():
            if new.get(key) is None:
                return False
            if key != 'args':
                unseen.append((old[key], new[key]))
            elif old[key] != new[key]:
                return False
        i += 1

    return True
