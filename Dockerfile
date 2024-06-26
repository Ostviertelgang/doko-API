# pull official base image
FROM python:3.11.4-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get -y install libpq-dev gcc
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh


# copy project
COPY . .

#EXPOSE 8000

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# run entrypoint.sh
ENTRYPOINT ["sh","/usr/src/app/entrypoint.sh"]