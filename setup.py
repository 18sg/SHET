#!/usr/bin/env python

from distutils.core import setup

setup(
    name='SHET',
    version='0.1',
    description='SHET House Event Tunnelling',
    author='The UHG Guys',
    url='http://github.com/tomjnixon/interSHET',
    package_dir = {'shet': 'src'},
    packages=['shet', 'shet.server', 'shet.client'],
    scripts=['scripts/shetserv'])
