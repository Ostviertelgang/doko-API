# Doppelkopf Counting Application API Server in Django

![Banner Picture](https://i.imgur.com/KHbifDD.png)
This is the doko-API Doppelkopf point counting suite backend server.
Doppelkopf is a german card game, that is played with 4 players in 2 teams. The goal is to get as many points as possible over a series of rounds.
More information about the game can be found [here](https://en.wikipedia.org/wiki/Doppelkopf).

The doko-suite does not implement the game itself, but is only a tool to keep track of the points of the players over a game (usually 16 rounds), as well as saving all time statistic and visualizing this data.

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


## Roadmap
Currently, I am working on release 1.0. which will include all basic features to count Doppelkopf points and manage players, as well as statics and CSV import/export.

Release 2.0 will be hardened for production deployment and will include authentication.

Further analysis features are planned for future releases.

#### old stuff
TZ in .env empty, try to get os tz, else utc

#### todos after test
1. csv importer (to be tested) defintions and how-to