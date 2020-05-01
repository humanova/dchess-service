from flask import Flask, url_for, render_template, request, send_file, redirect, jsonify
#import database
import random
from exceptions import InvalidUsage
from utils import ChessPNG
import confparser

config = confparser.get("config.json")
chess_png = ChessPNG(config.lichess_token)

app = Flask("dchess")


@app.route('/get_match')
def get_match():
    pass


@app.route('/create_match')
def create_match(pasta_id):
    pass


@app.route('/get_match_preview/<game_id>')
@app.route('/get_match_preview/<game_id>/<move>')
def get_match_preview(game_id, move):
    png_obj = None
    try:
        png_obj = chess_png.get_image_from_id(game_id, int(move))
    except Exception as e:
        raise InvalidUsage('incorrect game id', status_code=410)
    return send_file(png_obj, mimetype='image/png')


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def not_found(e):
    pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')