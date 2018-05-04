import drf_auto
import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()


setup(
    name='drf-auto',
    version=drf_auto.__version__,
    packages=['drf_auto'],
    license='Apache 2.0',  # Ставим лицензию
    description='Auto docs, auto tests, auto helpers for django rest framework. Python3.x, Django>=1.9',
    long_description=README,
    author='Deys Timofey',
    author_email='nxexox@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        "Django>=1.9",
        "djangorestframework>=3",
        "six>=1"
    ]
)
