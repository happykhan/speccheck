from setuptools import setup, find_packages
from speccheck import __version__, __name__

setup(
    name=__name__,
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'rich',
        'jinja2',
        'pandas',
        'requests',
        'plotly'
    ],
    extras_require={
        "dev": [
            "pytest",
            "coverage",
            "pylint",
        ]
    },
    entry_points={
        'console_scripts': [
            # Add command line scripts here
        ],
    },
)
