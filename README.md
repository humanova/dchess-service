# dChess API
## About
Chess service for Discord guilds.

Matches are played on lichess (account isn't necessary) and can be spectated. 
- Custom Global/Guild elo
- Player/guild stats
- Live board preview

## Example Client
![preview](https://media.discordapp.net/attachments/637381930488430594/712762969079152750/api_preview.png)
## API Endpoints

### *create_match* : **POST**
```
creates an open match and returns lichess api response data
```
```json
{
	"user_id" : 1234,
	"user_nick" : "humanovan",
	"opponent_id" : 1235,
	"opponent_nick" : "test_user",
	"guild_id" : 1337
}
```
### *update_match* : **POST**
```
updates player ids of an ongoing match
```
```json
{
	"match_id" : "4fpT7YFN",
	"match_result": "unfinished", 
	"white_id":1234,
	"black_id":1235 
}
```
### *update_match_end* : **POST**
```
if match is ended update match and player elos (if player ids are known)
```
```json
{
	"match_id" : "4fpT7YFN"
}
```
### *get_match_preview/<match_id>/<move>* : **GET**
```
requests match data, renders the board and returns a png object
```
```json
GET "example.com/dchess/api/get_match_preview/4fpT7YFN/11"
GET "example.com/dchess/api/get_match_preview/4fpT7YFN/last" 
```
### *get_match* : **POST**
```
returns match data
```
```json
{
	"match_id" : "4fpT7YFN"
}
``` 
### *get_player* : **POST**
```
returns player data
```

```json
{
	"player_id" : 1234
}
``` 

### *get_guild* : **POST**
```
returns guild data which consists of guild player ids and elos
```
```json
{
	"guild_id" : "544105274940850178"
}
``` 
