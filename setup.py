#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from shutil import rmtree
from setuptools import find_packages, setup, Command

NAME = 'jm-networking'
DESCRIPTION = 'A basic networking layer with async callbacks'
LONGDESCRIPTION = 'See the README.md file on GitHub for more information.'
URL = 'https://github.com/miller46/jm-networking'
EMAIL = 'jackmiller46@gmail.com'
AUTHOR = 'Jack Miller'
VERSION = '1.0.16'

REQUIRED = [
     'requests'
]


current_directory = os.path.abspath('pypi/')


class UploadCommand(Command):
    description = 'Build and publish this package with Pypi.'
    user_options = []

    @staticmethod
    def status(s):
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(current_directory, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel distribution...')
        os.system('{0} setup.py sdist bdist_wheel'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine...')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONGDESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    include_package_data=True,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    cmdclass={
        'upload': UploadCommand,
    },
)
