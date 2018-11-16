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
    url="https://github.com/OpenGeoVis/nuftio",
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
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        'Natural Language :: English',
    ),
)
