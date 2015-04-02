#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='SHET',
    version='1.0.2',
    description='SHET House Event Tunnelling',
    author='Thomas Nixon, Jonathan Heathcote',
    author_email='shet@tomn.co.uk',
    url='http://github.com/18sg/SHET',
    install_requires=["twisted"],
    packages=find_packages(exclude=["test"]),
    scripts=['scripts/shetserv'])
