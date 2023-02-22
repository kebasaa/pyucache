from setuptools import setup

setup(
    name='pyucache',
    version='0.1',
    author='Jonathan Muller',
    description='My Python library',
    packages=['pyucache'],
    classifiers=[
        'Development Status :: 3 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'asyncio',
        'logging',
        'datetime',
        'struct',
        'bleak',
    ],
)