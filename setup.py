from setuptools import setup, find_packages
from speccheck import __version__, __author__, __email__, __description__, __url__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Speccheck",
    version=__version__,
    author=__author__,
    description=__description__,
    author_email=__email__,
    url=__url__,
    long_description=long_description,
    long_description_content_type="text/markdown",
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
            "twine",
            "setuptools",
        ]
    },
    entry_points={
        'console_scripts': [
            'speccheck=speccheck:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bioinformatics",
    ],
    python_requires=">=3.10",
    license="GPLv3",
    keywords="genomics qc bioinformatics",
    project_urls={
        "Documentation": "https://github.com/happykhan/speccheck",
        "Source": "https://github.com/happykhan/speccheck",
        "Tracker": "https://github.com/happykhan/speccheck/issues",
    },    
)
