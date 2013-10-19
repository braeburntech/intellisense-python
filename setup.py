
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Don't import analytics-python module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'intellisense'))
from version import VERSION

long_description = '''
Intellisense API for Python.  Provides implementation for Caliper Sensor API and more

This is the official python client Intellisense REST API (http://www.intellifylearning.com).

'''

setup(
    name='intellisense-python',
    version=VERSION,
    url='https://github.com/pnayak/intellisense-python.git',
    author='Prashant Nayak',
    author_email='prashant@intellifylearning.com',
    maintainer='Intellify Learning',
    maintainer_email='founders@intellifylearning.com',
    packages=['intellisense'],
    license='MIT License',
    install_requires=[
        'requests',
        'python-dateutil'
    ],
    description='Intellisense API for Python.  Provides implementation for Caliper Sensor API and more',
    long_description=long_description
)
