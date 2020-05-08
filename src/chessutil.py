import chess
import chess.pgn
import chess.svg
import cairosvg
import berserk
import io


class ChessUtil:

    def __init__(self, token):
        session = berserk.TokenSession(token)
        self.client = berserk.Client(session=session)

    def create_match(self, clock_limit:int, clock_increment:int):
        try:
            return self.client.challenges.create_open(clock_limit=clock_limit, clock_increment=clock_increment)
        except:
            return None

    def get_game_data(self, id:str):
        try:
            return self.client.games.export(game_id=id)
        except:
            return None

    def get_preview_from_id(self, id:str, move:int):
        svg = self.get_svg_from_id(id, move_count=move)
        try:
            file_obj = cairosvg.svg2png(bytestring=svg, output_width=512, output_height=512)
            return io.BytesIO(file_obj)
        except Exception as e:
            print(e)
            return None

    def get_svg_from_id(self, id:str, move_count:int):
        match_pgn = self.client.games.export(game_id=id, as_pgn=True, clocks=False)
        m_counter = 0
        game = chess.pgn.read_game(io.StringIO(match_pgn))
        board = game.board()
        check = None
        if move_count >= 1:
            for move in game.mainline_moves():
                board.push(move)
                m_counter += 1
                if m_counter >= move_count:
                    break
        if board.is_check():
            check = board.king(board.turn)
        return chess.svg.board(board=board, check=check, coordinates=False)



