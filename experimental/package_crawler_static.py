import ast
import importlib
import os

class PackageNotFound(Exception):
    pass

def get_package_location(pkgname):
    """returns a dict containing info about modules, classes, functions"""
    spec = importlib.util.find_spec(pkgname)
    if spec is None:
        errmsg = ('Could not find "%s". Please make sure that '
                  'this package is installed.' % pkgname)
        raise PackageNotFound(errmsg)
    locations = [l for l in spec.submodule_search_locations]
    root_dir = locations[0]
    return root_dir

def get_package_info(root_dir):
    info = {}
    info['modules'] = {}
    subpackages = []
    for name in os.listdir(root_dir):
        if name.startswith('_'):
            continue
        elif name.endswith('.py'):
            path = os.path.join(root_dir, name)
            with open(path) as f:
                node = ast.parse(f.read(), path)
            modname = name[:-3]
            print(modname)
            info['modules'][modname] = get_module_info(node)
        elif not name.startswith('.'):
            subpackages.append(name)

    info['subpackages'] = {}
    for name in subpackages:
        path = os.path.join(root_dir, name)
        info['subpackages'][name] = get_package_info(path)

    return info

def get_module_info(node):
    """returns a dict containing info on classes and functions"""
    classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
    functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]

    res = {}
    res['classes'] = get_class_info(classes)
    res['functions'] = get_function_info(functions)

    return res

def get_class_info(classes):
    """returns a dict containing info on args, subclasses and functions"""
    res = {}
    for node in classes:
        if node.name.startswith('_') or res.get(node.name) is not None:
            continue

        # assumes that bases are user-defined within the same module
        init_func, subclasses, functions = _get_class_attrs(node, classes)
        args = []
        if init_func is not None:
            args = get_args(init_func.args)

        res[node.name] = {}
        res[node.name]['args'] = args
        # res[node.name]['bases'] = _get_basenames(node.bases)
        res[node.name]['subclasses'] = get_class_info(subclasses)
        res[node.name]['functions'] = get_function_info(functions)

    return res

def _get_class_attrs(node, classes):
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
    bases = {n.name:n for n in classes if n.name in basenames}
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
        # for testing, will delete later
        else:
            print(n)
            from pdb import set_trace; set_trace()
        res.append('.'.join(name[::-1]))
    return res

def get_function_info(functions):
    """returns a dict mapping function name to function args"""
    res = {}
    for node in functions:
        fname = node.name
        if fname.startswith('_') or res.get(fname) is not None:
            continue
        res[fname] = {}
        res[fname]['args'] = get_args(node.args)
    return res

def get_args(node):
    args = []
    for arg in node.args:
        if isinstance(arg, ast.arg):
            args.append(arg.arg)
        elif isinstance(arg, ast.Name):
            args.append(arg.id)
        # Testing - will delete later
        else:
            from pdb import set_trace; set_trace()
    return args

