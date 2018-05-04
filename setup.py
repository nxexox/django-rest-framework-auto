import drf_auto
import os

from setuptools import setup, find_packages


README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()


setup(
    name=drf_auto.__title__,
    version=drf_auto.__version__,
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    license='Apache 2.0',  # Ставим лицензию
    description='Auto docs, auto tests, auto helpers for Django REST Framework. Python3.x, Django>=1.9',
    long_description=README,
    url=drf_auto.__url__,
    author=drf_auto.__author__,
    author_email=drf_auto.__email__,
    maintainer=drf_auto.__author__,
    maintainer_email=drf_auto.__email__,
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
