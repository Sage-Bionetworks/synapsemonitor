"""Setup"""
import os
from setuptools import setup, find_packages

# figure out the version
# about = {}
# here = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(here, "synapsemonitor", "__version__.py")) as f:
#     exec(f.read(), about)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='synapsemonitor',
      # version=about["__version__"],
      version="0.0.2",
      description='Synapse monitoring',
      url='https://github.com/Sage-Bionetworks/synapseMonitor',
      author='Larsson Omberg, Thomas Yu',
      author_email='thomasyu888@gmail.com',
      long_description=long_description,
      long_description_content_type="text/markdown",
      license='Apache',
      packages=find_packages(),
      zip_safe=False,
      python_requires='>=3.6, <3.9',
      entry_points={'console_scripts': ['synapsemonitor = synapsemonitor.__main__:main']},
      install_requires=['synapseclient', 'pandas'])
