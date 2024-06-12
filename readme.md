# Doppelkopf Counting Application API Server in Django

![Banner Picture](https://i.imgur.com/KHbifDD.png)
This is the doko-API Doppelkopf point counting suite backend server.
Doppelkopf is a german card game, that is played with 4 players in 2 teams. The goal is to get as many points as possible over a series of rounds.
More information about the game can be found [here](https://en.wikipedia.org/wiki/Doppelkopf).

The doko-suite does not implement the game itself, but is only a tool to keep track of the points of the players over a game (usually 16 rounds), as well as saving all time statistic and visualizing this data.

This component is the backend server, implemented in Django Rest Framework.
It provides a REST API to the frontend, which currently is a Discord python bot you can find [here](https://github.com/Ostviertelgang/doko-Discord-Bot).
There are more frontends planned; currently a Svelte frontend is in development.


## Installation
Currently, the API is not yet released, but you can run it locally.

Once the API is released, you can install it with docker-compose and a dockerhub image.






#### old stuff
TZ in .env empty, try to get os tz, else utc

#### todos after test
2. test bockrunden undo but should work
3. csv importer (to be tested)