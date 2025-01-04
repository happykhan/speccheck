# speccheck
a bioinformatics software focused on quality control based on species criteria


run from docker 
```
docker run  speccheck /app/speccheck.py  --help 
```


build from docker
```
docker login && docker build  --platform linux/amd64 -t happykhan/speccheck:0.1 -f docker/Dockerfile . && docker push happykhan/speccheck:0.1  
```