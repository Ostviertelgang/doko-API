# Doppelkopf Counting Application API Server in Django

![Banner Picture](https://i.imgur.com/KHbifDD.png)
This is the doko-API Doppelkopf point counting suite backend server.
Doppelkopf is a german card game, that is played with 4 players in 2 teams. The goal is to get as many points as possible over a series of rounds.
More information about the game can be found [here](https://en.wikipedia.org/wiki/Doppelkopf).

The doko-suite does not implement the game itself, but is only a tool to keep track of the points of the players over a game (usually 16 rounds), as well as saving all time statistic and visualizing this data.
If you search for a good implementation of the game itself, which works well with this project, I would recommend [doko3000](https://github.com/HenriWahl/doko3000), which can accomodate all rulesets.

This component is the backend server, implemented in Django Rest Framework.
It provides a REST API to the frontend, which currently is a Discord python bot you can find [here](https://github.com/Ostviertelgang/doko-Discord-Bot).
There are more frontends planned; currently a Svelte frontend is in development.

## Features
1. Perform the point counting for a game of Doppelkopf, with solo, bockrunden, and pflichtsolo support with an open design philosophy to accomdate all possible rulesets.
2. Keep track of longterm staticts to see who always looses.
3. Integrate different frontends (including your own!) with the REST API. Currently, a [Discord Bot](https://github.com/Ostviertelgang/doko-Discord-Bot) is available and a Web Svelte frontend is in development.
4. Import and export games and players via CSV files, if you already have your all-time stats in a spreadsheet.

## Installation
Currently, the API is not yet released, but you can run it locally.
I have the API already deployed and its working fine, but I want to finalize the API before releasing it.

Once the API is released, you can install it with docker-compose and a dockerhub image.

### Build yourself
```bash
chmod +x ./entrypoint.prod.sh
docker-compose -f docker-compose.prod.yml up -d --build  
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput 
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear
```


### The prod.env file
Some fields will be preset with default values, but you also should change some values. Here is an overview:
```bash
SECRET_KEY=CHANGE ME # change this to a secure key
DJANGO_ALLOWED_HOSTS='nginx' # These are the allowed hosts for the django server. You can change the "nginx" to the name of your nginx container, or, depending on your setup, to the domain of your website.
DEBUG=0 # set to 1 for debugging
SQL_ENGINE=django.db.backends.postgresql # don't change this, postgres is the only supported database
SQL_DATABASE=doko # you can change this however you like, but it is not necessary. Also change in the prod.db.env
SQL_USER=hello_django # change this to a secure username. Also change in the prod.db.env
SQL_PASSWORD=hello_django # change this to a secure password. Also change in the prod.db.env
SQL_HOST=db # name of the postgres container. Don't change unless you know what you are doing
SQL_PORT=5432 # default port for postgres. Don't change unless you know what you are doing
TIME_ZONE= # can be left empty, will default system time zone, if this does not work to UTC
API_URL= # your website url, where the API is hosted, for CORS
```
Don't forget to change the values in the prod.db.env file as well, if you change the SQL_DATABASE, SQL_USER, or SQL_PASSWORD, which is advisable.


## Roadmap
Currently, I am working on release 1.0. which will include all basic features to count Doppelkopf points and manage players, as well as statics and CSV import/export.

Release 2.0 will be hardened for production deployment and will include authentication.

Further analysis features are planned for future releases.
