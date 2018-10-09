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

"""A set of functions that aid in crawling a package
and creating a corresponding data model"""

import ast
import importlib
import os


class PackageNotFound(Exception):
    pass


def get_package_location(pkgname):
    """gets the package location

    Args:
        pkgname: the package name as a string

    Returns:
        A string containing the path of the give package

    Raises:
        PackageNotFound: An error that occurs when the package is not found
    """
    spec = importlib.util.find_spec(pkgname)
    if spec is None:
        errmsg = ('Could not find "%s". Please make sure that '
                  'this package is installed.' % pkgname)
        raise PackageNotFound(errmsg)
    locations = [l for l in spec.submodule_search_locations]
    root_dir = locations[0]
    return root_dir


def get_package_info(root_dir):
    """gets package info

    Crawls the package directory with filesystem tooling and
    creates a data model containing relevant info about
    subpackages, modules, classes, functions, and args

    Args:
        root_dir: the location of the package

    Returns:
        A dict mapping keys to the corresponding data derived
        For example:
        {
            module_name: {
                'classes': {
                    class_name: {
                        'args': [arg1, arg2, ...],
                        'functions': {
                            function_name: {'args': [...]},
                        }
                    },
                    class_name: {...},
                },
                'functions': {...},
                'subclasses': {...},
            },
            'subpackages': {...}
        }
    """

    info = {}
    info['modules'] = {}
    subpackages = []
    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)
        if name.startswith('_'):
            continue
        elif name.endswith('.py'):
            if (name.startswith('test_') or name.endswith('_test.py')):
                continue
            with open(path) as f:
                node = ast.parse(f.read(), path)
            modname = os.path.splitext(name)[0]
            info['modules'][modname] = get_module_info(node)
        elif os.path.isdir(path) and not name.startswith('.'):
            subpackages.append(name)

    info['subpackages'] = {}
    for name in subpackages:
        path = os.path.join(root_dir, name)
        info['subpackages'][name] = get_package_info(path)

    return info


def get_module_info(node):
    """gets module info

    Recursively crawls the ast node and creates a data model
    containing relevant info about the module's classes,
    subclasses, functions, and args

    Args:
        node: the module

    Returns:
        A dict mapping keys to the corresponding data derived
        For example:
        {
            'classes': {
                class_name: {
                    'args': [arg1, arg2, ...],
                    'functions': {
                        function_name: {'args': [...]},
                    }
                },
                class_name: {...},
            },
            'functions': {...},
            'subclasses': {...},
        }
    """
    classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
    functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]

    res = {}
    res['classes'] = _get_class_info(classes)
    res['functions'] = _get_function_info(functions)

    return res


def _get_class_info(classes):
    """returns a dict containing info on args, subclasses and functions"""
    res = {}
    for node in classes:
        # in classes with multiple base classes, there may be subclasses or
        # functions that overlap (share the same name), to mirror the actual
        # pythonic behavior, clashes are ignored
        if node.name.startswith('_') or res.get(node.name) is not None:
            continue

        # assumption is that bases are user-defined within the same module
        init_func, subclasses, functions = _get_class_attrs(node, classes)
        args = []
        if init_func is not None:
            args = _get_args(init_func.args)

        res[node.name] = {}
        res[node.name]['args'] = args
        res[node.name]['subclasses'] = _get_class_info(subclasses)
        res[node.name]['functions'] = _get_function_info(functions)

    return res


def _get_class_attrs(node, classes):
    """returns operational init func, subclasses, and functions of a class
    including those of any base classes defined within the same module by
    crawling through class nodes
    """
    init_func, subclasses, functions = None, [], []
    for n in node.body:
        if hasattr(n, 'name') and n.name == '__init__':
            init_func = n
        if isinstance(n, ast.ClassDef):
            subclasses.append(n)
        elif isinstance(n, ast.FunctionDef):
            functions.append(n)

    # inheritance priority is preorder
    basenames = _get_basenames(node.bases)
    bases = {n.name: n for n in classes if n.name in basenames}
    for bname in basenames:
        if bases.get(bname) is None:
            continue
        n = bases[bname]
        _init_func, _subclasses, _functions = _get_class_attrs(n, classes)
        if init_func is None:
            init_func = _init_func
        subclasses.extend(_subclasses)
        functions.extend(_functions)
    return (init_func, subclasses, functions)


def _get_basenames(bases):
    res = []
    for n in bases:
        name = []
        if isinstance(n, ast.Attribute):
            while isinstance(n, ast.Attribute):
                name.append(n.attr)
                n = n.value
        if isinstance(n, ast.Name):
            name.append(n.id)
        res.append('.'.join(name[::-1]))
    return res


def _get_function_info(functions):
    """returns a dict mapping function name to function args"""
    res = {}
    for node in functions:
        fname = node.name
        if fname.startswith('_') or res.get(fname) is not None:
            continue
        res[fname] = {}
        res[fname]['args'] = _get_args(node.args)
    return res


def _get_args(node):
    """returns a list of args"""
    args = []
    for arg in node.args:
        if isinstance(arg, ast.arg):
            args.append(arg.arg)
        elif isinstance(arg, ast.Name):
            args.append(arg.id)
    return args
