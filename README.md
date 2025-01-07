# speccheck

[![Run Pytest](https://github.com/happykhan/speccheck/actions/workflows/run_pytest.yml/badge.svg)](https://github.com/happykhan/speccheck/actions/workflows/run_pytest.yml)
[![GPLv3 License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python->=3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)

a bioinformatics software focused on quality control based on species criteria


run from docker 
```
docker run  speccheck /app/speccheck.py  --help 
```


build from docker
```
docker login && docker build  --platform linux/amd64 -t happykhan/speccheck:0.1 -f docker/Dockerfile . && docker push happykhan/speccheck:0.1  
```