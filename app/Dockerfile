# pull official base image
FROM python:slim

# set work directory
WORKDIR /usr/src/app

# create directory for db
RUN mkdir -p /usr/src/db

# copy project
COPY . .

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# run entrypoint.sh
ENTRYPOINT ["python3", "main.py"]