from flask import Flask, url_for, render_template, request, send_file, redirect, jsonify
from playhouse.shortcuts import model_to_dict
import database
import random
import exceptions
from utils import ChessUtil
import confparser

config = confparser.get("config.json")
chess_util = ChessUtil(config.lichess_token)
db = database.DB()
app = Flask("dchess")


@app.route('/dchess/api/get_match', methods=['POST'])
def get_match():
    id = request.json["match_id"]
    try:
        m = db.get_match_by_id(id)
        if m is not None:
            match = chess_util.get_game_data(id=id)
            db_match = model_to_dict(m)
            return jsonify(dict(success=True, match=match, db_match=db_match))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except Exception as e:
        print(e)
        return jsonify(dict(success=False))


@app.route('/dchess/api/update_match', methods=['POST'])
def update_match():
    id = request.json["match_id"]
    result = request.json["match_result"]
    try:
        white_id = request.json["white_id"]
        black_id = request.json["black_id"]
    except:
        white_id = None
        black_id = None
    try:
        m = db.get_match_by_id(id)
        if m is not None:
            db.update_match(match_id=id, result=result, white_id=white_id, black_id=black_id)

            match = chess_util.get_game_data(id=id)
            db_match = model_to_dict(m)
            return jsonify(dict(success=True, match=match, db_match=db_match))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except:
        return jsonify(dict(success=False))


@app.route('/dchess/api/create_match', methods=['POST'])
def create_match():
    user_id = request.json['user_id']
    user_nick = request.json['user_nick']
    opponent_id = request.json['opponent_id']
    opponent_nick = request.json['opponent_nick']
    guild_id = request.json['guild_id']

    if db.get_guild_by_id(guild_id) is None:
        db.add_guild(guild_id)

    if db.get_player_by_id(user_id) is None:
        db.add_player(player_id=user_id, player_nick=user_nick)

    if db.get_player_by_id(opponent_id) is None:
        db.add_player(player_id=opponent_id, player_nick=opponent_nick)

    try:
        game = chess_util.client.challenges.create_open(clock_limit=300, clock_increment=3)
        id = game['challenge']['id']
        db_match = db.add_match(match_id=id, guild_id=guild_id)
        return jsonify(dict(success=True, match=game, db_match = model_to_dict(db.get_match_by_id(id))))
    except Exception as e:
        print(e)
        return jsonify(dict(success=False))


@app.route('/dchess/api/get_match_preview/<game_id>/<move>')
@app.route('/dchess/api/get_match_preview/<game_id>/<move>.png')
def get_match_preview(game_id, move):
    if move == "last":
        move = 999
    if int(move) >= 0:
        png_obj = None
        try:
            png_obj = chess_util.get_image_from_id(game_id, int(move))
        except Exception as e:
            raise exceptions.InternalError(e, status_code=400)
        return send_file(png_obj, mimetype='image/png')
    else:
        raise exceptions.InvalidUsage("Invalid move number", status_code=400)


@app.route('/dchess/api/get_player', methods=['POST'])
def get_player():
    id = request.json["player_id"]
    try:
        player = db.get_player_by_id(id)
        if player is not None:
            return jsonify(dict(success=True, player=model_to_dict(player)))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except Exception as e:
        print(e)
        return jsonify(dict(success=False))

@app.errorhandler(exceptions.InvalidUsage)
@app.errorhandler(exceptions.InternalError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def not_found(e):
    pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1338)