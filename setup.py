#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Setup script for speccheck.

This setup.py is maintained for backward compatibility.
The primary configuration is in pyproject.toml.
Modern pip installations will use pyproject.toml directly.
"""
import os

from setuptools import find_packages, setup





# Read version from speccheck/__init__.py
def get_version():
    init_file = os.path.join(os.path.dirname(__file__), 'speccheck', '__init__.py')
    with open(init_file, encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '0.0.0'


# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, encoding='utf-8') as f:
            return f.read()
    return ''


# For modern pip (>=10), configuration is read from pyproject.toml
# This setup() call provides backward compatibility
setup(
    name='speccheck',
    version=get_version(),
    description='A bioinformatics software focused on quality control based on species criteria',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Nabil-Fareed Alikhan',
    author_email='nabil@happykhan.com',
    url='https://github.com/happykhan/speccheck',
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.10',
    install_requires=[
        'rich>=13.0.0',
        'jinja2>=3.0.0',
        'pandas>=2.0.0',
        'requests>=2.28.0',
        'plotly>=5.0.0',
        'typer>=0.9.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'coverage>=7.0.0',
            'pylint>=2.15.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'ruff>=0.1.0',
            'bandit>=1.7.0',
            'safety>=2.3.0',
            'pre-commit>=3.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'speccheck=speccheck:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Bioinformatics',
    ],
    license='GPLv3',
    keywords=['genomics', 'qc', 'bioinformatics', 'quality-control', 'genomic-analysis'],
    project_urls={
        'Homepage': 'https://github.com/happykhan/speccheck',
        'Documentation': 'https://github.com/happykhan/speccheck',
        'Bug Tracker': 'https://github.com/happykhan/speccheck/issues',
        'Source': 'https://github.com/happykhan/speccheck',
    },
)
