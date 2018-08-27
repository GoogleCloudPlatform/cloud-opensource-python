# Release Compatibility_Lib

## Steps

### Update the version number in `setup.py`

### Build the Python wheel

```
python setup.py bdist_wheel
```

### Upload the package to PyPI using twine

```
# If not installed
pip install twine

# Running the command below needs a PyPI user account which owns this library
twine upload dist/*
```

### Create a Github release
