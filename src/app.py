from flask import Flask, request, send_file, jsonify, abort, render_template
from playhouse.shortcuts import model_to_dict
import database
import random
import exceptions
from utils import ChessUtil
import confparser

config = confparser.get("config.json")
chess_util = ChessUtil(config.lichess_token)
db = database.DB()
app = Flask("dchess", template_folder="src/templates")


@app.route('/dchess/api/get_match', methods=['POST'])
def get_match():
    id = request.json["match_id"]
    try:
        m = db.get_match_by_id(id)
        if m is not None:
            match = chess_util.get_game_data(id=id)
            if match is not None:
                db_match = model_to_dict(m)
                return jsonify(dict(success=True, match=match, db_match=db_match))
            return jsonify(dict(success=False, reason="match didn't start"))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except Exception as e:
        print(e)
        return jsonify(dict(success=False))


@app.route('/dchess/api/update_match', methods=['POST'])
def update_match():
    if not request.host == config.coordinator_host:
        abort(403)
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


@app.route('/dchess/api/update_match_end', methods=['POST'])
def update_match_end():
    if not request.host == config.coordinator_host:
        abort(403)
    id = request.json["match_id"]
    try:
        m = db.get_match_by_id(id)
        if m is not None:
            match_data = chess_util.get_game_data(id=id)
            updated_data = db.update_match_end(match_id=id, data=match_data)
            return jsonify(dict(success=True, data=updated_data))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except:
        return jsonify(dict(success=False))


@app.route('/dchess/api/create_match', methods=['POST'])
def create_match():
    if not request.host == config.coordinator_host:
        abort(403)
    user_id = request.json['user_id']
    user_nick = request.json['user_nick']
    opponent_id = request.json['opponent_id']
    opponent_nick = request.json['opponent_nick']
    guild_id = request.json['guild_id']

    # default
    clock_limit = 300
    clock_increment = 3
    try:
        if request.json['clock_minutes'] and request.json['clock_increment']:
            clock_limit = request.json['clock_minutes'] * 60
            clock_increment = request.json['clock_increment']
    except:
        pass

    # bunch of db checks :(
    # todo : pls fix
    if db.get_guild_by_id(guild_id) is None:
        db.add_guild(guild_id)

    if db.get_player_by_id(user_id) is None:
        db.add_player(player_id=user_id, player_nick=user_nick)
    if db.get_guild_player_by_id(guild_id=guild_id, player_id=user_id) is None:
        db.add_guild_player(guild_id=guild_id, player_id=user_id)

    if db.get_player_by_id(opponent_id) is None:
        db.add_player(player_id=opponent_id, player_nick=opponent_nick)
    if db.get_guild_player_by_id(guild_id=guild_id, player_id=opponent_id) is None:
        db.add_guild_player(guild_id=guild_id, player_id=opponent_id)
    try:
        game = chess_util.client.challenges.create_open(clock_limit=clock_limit, clock_increment=clock_increment)
        id = game['challenge']['id']
        db.add_match(match_id=id, guild_id=guild_id)
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
            return send_file(png_obj, mimetype='image/png')
        except Exception as e:
            return jsonify(dict(success=False))
    else:
        return jsonify(dict(success=False, reason="invalid match id"))


@app.route('/dchess/api/get_player', methods=['POST'])
def get_player():
    id = request.json["player_id"]
    guild_id = None
    try:
        if request.json["guild_id"]:
            guild_id = request.json["guild_id"]
    except:
        pass
    try:
        stats = db.get_player_stats(player_id=id, guild_id=guild_id)
        if stats is not None:
            if guild_id:
                return jsonify(dict(success=True, player=stats['player'], guild_player=stats['guild_player']))
            else:
                return jsonify(dict(success=True, player=stats['player']))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except Exception as e:
        print(e)
        return jsonify(dict(success=False))


@app.route('/dchess/api/get_guild', methods=['POST'])
def get_guild():
    guild_id = request.json["guild_id"]
    try:
        stats = db.get_guild_stats(guild_id=guild_id)
        if stats is not None:
            return jsonify(dict(success=True, guild=stats))
        else:
            return jsonify(dict(success=False, reason="invalid match id"))
    except Exception as e:
        print(e)
        return jsonify(dict(success=False))


@app.errorhandler(403)
def handle_forbidden(e):
    return render_template("error.html", error_code="403")


@app.errorhandler(404)
def handle_not_found(e):
    return render_template("error.html", error_code="404")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1338)