#!/usr/bin/env python

from distutils.core import setup

setup(
    name='SHET',
    version='1.0.1',
    description='SHET House Event Tunnelling',
    author='Thomas Nixon, Jonathan Heathcote',
    author_email='shet@tomn.co.uk',
    url='http://github.com/18sg/SHET',
    package_dir = {'shet': 'src'},
    packages=['shet', 'shet.server', 'shet.client', 'shet.path'],
    scripts=['scripts/shetserv'])
