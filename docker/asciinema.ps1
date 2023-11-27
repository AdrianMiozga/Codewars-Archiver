docker build --file "docker/Dockerfile.asciinema" --tag image .
docker run --rm -it --volume="$PWD/docker/volume:/root/app" image
