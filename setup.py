import os
from setuptools import setup, find_packages

PKG = 'snapraid-runner'
######
setup(
    name=PKG,
    version=f"0.0.{os.environ.get('BUILD_ID', 1)}",
    description='Python script for SnapRAID cronjobs',
    long_description='',
    keywords='snapraid, sync, scrub',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(include=["snapraid.*"]),
    include_package_data=True,
    long_description_content_type='text/markdown',
    package_data={},
    author='marwinfaiter',
    author_email='noobgubbe@gmail.com',
    url='https://github.com/marwinfaiter/snapraid-runner',
    entry_points={
        'console_scripts': [
            'snapraid-runner = snapraid.runner:main',
        ]
    },
    classifiers=[  # Please update this. Possibilities: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Development Status :: 4 - Beta',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',

        'Operating System :: OS Independent',

        'Topic :: Internet',
        'Topic :: Software Development',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',

    ],
    zip_safe=False,
    install_requires=[
        "typed-argument-parser",
        "pyyaml",
        "attrs",
        "cattrs",
        "discord",
    ],
    extras_require={
        "test": [
            "mypy",
            "pytest",
            "pylint",
            "mockito"
        ]
    }
)
