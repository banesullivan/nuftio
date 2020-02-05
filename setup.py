"""``nuftio``: File I/O for NUFT simulations
"""

import setuptools

__version__ = '0.0.0'

with open("README.rst", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="nuftio",
    version=__version__,
    author="Bane Sullivan",
    author_email="info@pvgeo.org",
    description="File I/O for NUFT simulations",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/banesullivan/nuftio",
    packages=setuptools.find_packages(),
    install_requires=[
        'cPyparsing',
        'numpy',
        'pandas',
        'xmltodict',
        'properties',
        'discretize',
    ],
    classifiers=(
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ),
)
