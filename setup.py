from setuptools import setup

version = {}
with open("synapsemonitor/__version__.py") as fp:
    exec(fp.read(), version)

setup(
    version=version["__version__"]
)
