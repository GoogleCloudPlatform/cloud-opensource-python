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

import enum
from compatibility_lib import package_crawler_static as crawler


class _Error(enum.Enum):
    MISSING = '%s: missing arg "%s"'
    NUM_TOTAL = '%s: expected %s args, got %s'
    NUM_REQUIRED = '%s: expected %s required args, got %s'
    BAD_ARG = '%s: bad arg name; expected "%s", got "%s"'
    BAD_VALUE = ('%s: default value was not preserved; '
                 'expecting "%s=%s", got "%s=%s"')


# TODO: This needs more sophisticated logic
def check(old_dir, new_dir):
    """checks for semver breakage for two local directories
    it looks at all the attributes found by get_package_info
    (module, class, function names) for old_dir and making sure they are also
    in new_dir in a BFS

    Args:
        old_dir: directory containing old files
        new_dir: directory containing new files

    Returns:
        A list of error strings describing semver breakages
    """
    qn = ()
    old_pkg_info = crawler.get_package_info(old_dir)
    new_pkg_info = crawler.get_package_info(new_dir)

    unseen = [(qn, old_pkg_info, new_pkg_info)]
    errors = []

    i = 0
    while i < len(unseen):
        qn, old, new = unseen[i]
        for key in old.keys():
            if new.get(key) is None:
                msg = _Error.MISSING.value
                errors.append(msg % (_get_qn_str(qn), key))
                continue
            if key != 'args':
                new_qn = qn + (key,)
                unseen.append((new_qn, old[key], new[key]))
            else:
                # TODO: better error messages
                new_errors = _check_args(qn, old[key], new[key])
                errors.extend(new_errors)
        i += 1

    return errors


def _get_qn_str(qn_list):
    """returns the qualified name string"""
    clean_qn = [name for i, name in enumerate(qn_list) if i % 2 == 1]
    res = '.'.join(clean_qn)
    return res


def _check_args(qn_list, old_args, new_args):
    errors = []
    qn = _get_qn_str(qn_list)
    missing = _Error.MISSING.value.replace('%s', qn, 1)
    num_total = _Error.NUM_TOTAL.value.replace('%s', qn, 1)
    num_required = _Error.NUM_REQUIRED.value.replace('%s', qn, 1)
    bad_arg = _Error.BAD_ARG.value.replace('%s', qn, 1)
    bad_value = _Error.BAD_VALUE.value.replace('%s', qn, 1)

    # check old args against new args
    old_single_args = old_args['single_args']
    new_single_args = new_args['single_args']
    if len(old_single_args) > len(new_single_args):
        res = [num_total % (len(old_single_args), len(new_single_args))]
        return res
    for i, _ in enumerate(old_single_args):
        if old_single_args[i] != new_single_args[i]:
            res = [bad_arg % (old_single_args[i], new_single_args[i])]
            return res

    old_defaults = old_args['defaults']
    new_defaults = new_args['defaults']
    num_old_req_args = len(old_single_args) - len(old_defaults)
    num_new_req_args = len(new_single_args) - len(new_defaults)

    # check required args match up
    for i in range(max(num_old_req_args, num_new_req_args)):
        if i == len(old_single_args) or i == len(new_single_args):
            msg = num_required % (num_old_req_args, num_new_req_args)
            errors.append(msg)
            break

        # if old_single_args[i] != new_single_args[i]:
        #     msg = bad_arg % (old_single_args[i], new_single_args[i])
        #     errors.append(msg)
        #     break

    # check default arg values
    for key in old_defaults:
        if key not in new_defaults:
            errors.append(missing % key)
        if old_defaults[key] != new_defaults[key]:
            errors.append(bad_value % (key, old_defaults[key],
                                       key, new_defaults[key]))

    # check vararg and kwarg
    if old_args['vararg'] and old_args['vararg'] != new_args['vararg']:
        errors.append(missing % old_args['vararg'])
    if old_args['kwarg'] and old_args['kwarg'] != new_args['kwarg']:
        errors.append(missing % old_args['kwarg'])

    return errors
