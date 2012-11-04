#!/usr/bin/env python

from distutils.core import setup, Extension

pytadbit_module = Extension('pytadbit.tadbit_py',
                     sources=['tadbit_py.c'],
                     )

setup(
    name        = 'pytadbit',
    version     = '1.0',
    author      = 'Guillaume Filion',
    description = 'Identify TADs in hi-C data',
    ext_modules = [pytadbit_module],
    package_dir = {'pytadbit': '../pytadbit'},
    packages    = ['pytadbit'],
    py_modules  = ["pytadbit"],
)
