# How to use the csv interfaces
The doko-API offers an interface to import and export games and players via CSV files. This is useful if you already have your all-time stats in a spreadsheet and want to import them into the doko-API, or if you want to export the data to analyze it youself and for backup and update purposes.

## export CSV
Just call the endpoint '/get_export/' with a GET request. The server will then return a CSV file with all games and players in the database in the following format:

```csv
game_id,game_name,is_closed,created_at,closed_at,player1,player2,player3,player4
123456,Thursdayround,True,2021-01-01T01:00:00+00:00,2021-01-01T01:10:00+00:00,10,-13,5,-2
```
Where the first row is the header and the following rows are the data. The first column is the game_id, the second the game_name, the third if the game is closed, the fourth the creation date, and the following columns are the points of the players in the game.

## Import CSV
To import a CSV file, you have to send a POST request to the endpoint '/import_csv/' with the CSV file as a form-data file. The file should be in the same format as the export CSV file, while the order does not matter. 
Example:

```csv
game_id,game_name,is_closed,created_at,closed_at,player1,player2,player3,player4
123456,Thursdayround,True,2021-01-01T01:00:00+00:00,2021-01-01T01:10:00+00:00,10,-13,5,-2
```

The server will then import the data into the database. The response will be a JSON object with the number of games and players imported.

By default, the API will check if games are duplicates on basis of the 'game_id'.
However, you can enable the 'create_game_duplicates_based_on_ids' flag in the request body to ignore the game_id based duplicate check and just generate a new game_id for the games. 

Currently, the import endpoint is not implemented in any public frontend, except for the swagger UI of the API itself.