#!/usr/bin/env python

from distutils.core import setup

setup(
    name='interSHET',
    version='0.1',
    description='Spiffing House Event Tunnelling',
    author='The UHG Guys',
    url='http://github.com/tomjnixon/interSHET',
    package_dir = {'shet': 'src'},
    packages=['shet', 'shet.server'],
    scripts=['scripts/shetserv'])
