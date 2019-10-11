# Readme
# Build image from repo root: docker build -t <name>:<version> -f src/deploy/docker/Dockerfile .
# Start container: docker container run --publish 8000:8000 --detach --name <container name> <image name>:<tag>

# Python 3.6.9 Base image
FROM python:3.6.9

WORKDIR /app

# Add and install requirements
add requirements.txt requriements.txt

# Add project files
add src src/

WORKDIR src/voluntyrBackend/

RUN pip3 install -r /app/requriements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]