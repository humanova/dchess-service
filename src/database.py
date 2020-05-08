from peewee import *
import time
from logger import logging
from playhouse.shortcuts import model_to_dict

ELO_CONSTANT = 32
db = SqliteDatabase("db/dchess.db")


class BaseModel(Model):
    class Meta:
        database = db


class Player(BaseModel):
    id = CharField(unique=True)
    nickname = CharField()
    matches = IntegerField()
    wins = IntegerField()
    loses = IntegerField()
    draws = IntegerField()
    last_match_id = CharField()
    last_match_date = DateTimeField()
    elo = FloatField()  # general elo


class Match(BaseModel):
    id = CharField(unique=True)
    guild_id = IntegerField()
    white_player_id = IntegerField()
    black_player_id = IntegerField()
    match_date = DateTimeField()
    result = CharField()
    result_code = CharField()


class Guild(BaseModel):
    id = CharField(unique=True)


class GuildPlayer(BaseModel):
    player_id = CharField()
    guild_id = CharField()
    elo = FloatField() # guild ranking elo


class DB:

    def __init__(self):
        self.connected = False
        self.init_tables()

    def init_tables(self):
        try:
            db.create_tables([Player, Match, Guild, GuildPlayer])
        except Exception as e:
            logging.exception(f"[DB] Couldn't create tables, it may already exist in db : {e})")

    def connect(self):
        try:
            db.connect()
            self.connected = True
        except Exception as e:
            logging.exception(f"[DB] Couldn't connect to db : {e}")

    def add_player(self, player_id, player_nick):
        try:
            with db.atomic():
                player = Player.create(
                    id=player_id,
                    nickname=player_nick,
                    matches=0,
                    wins=0,
                    loses=0,
                    draws=0,
                    last_match_id="",
                    last_match_date=time.time(),
                    elo=1500.0
                )
                # logging.info(f"new player -> : {player_id}")
                return player
        except Exception as e:
            logging.exception(f'[DB] Error while adding player : {e}')

    def add_match(self, match_id, guild_id, white_id=-1, black_id=-1, match_ts=time.time(), result="unfinished"):
        try:
            with db.atomic():
                match = Match.create(
                    id=match_id,
                    guild_id=guild_id,
                    white_player_id=white_id,
                    black_player_id=black_id,
                    match_date=match_ts,
                    result=result,
                    result_code="?"
                )
                # logging.info(f"new match -> : {match_id}")
                return match
        except Exception as e:
            logging.exception(f'[DB] Error while adding match : {e}')

    def add_guild(self, guild_id):
        try:
            with db.atomic():
                guild = Guild.create(
                    id=guild_id
                )
                # logging.info(f"new guild -> : {g_id}")
                return guild
        except Exception as e:
            logging.exception(f'[DB] Error while adding guild : {e}')

    def add_guild_player(self, guild_id, player_id):
        try:
            with db.atomic():
                guild_pl = GuildPlayer.create(
                    guild_id=guild_id,
                    player_id=player_id,
                    elo=1500.0
                )
                # logging.info(f"new guild_player -> : {player_id}")
                return guild_pl
        except Exception as e:
            logging.exception(f'[DB] Error while adding guild_player : {e}')

    def update_match(self, match_id, result, result_code=None, white_id=None, black_id=None):
        try:
            m = self.get_match_by_id(match_id)
            m.result = result
            if not result_code == None:
                m.result_code = result_code
            if not white_id == None and not black_id == None:
                m.white_player_id = white_id
                m.black_player_id = black_id
            m.save(only=[Match.result, Match.white_player_id, Match.black_player_id, Match.result_code])
            logging.info(f'[DB] Match:{match_id} has been updated')
        except Exception as e:
            logging.exception(f'[DB] Error while updating match:{match_id} {e}')

    # updates match and player(if known) stats
    def update_match_end(self, match_id, data):
        try:
            m = self.get_match_by_id(match_id)
            if m.result == "unfinished":
                status = data["status"]
                result_code = self.get_result_code(match_data=data)
                self.update_match(match_id=match_id, result=status, result_code=result_code)

                # if we know player ids update their stats
                if not m.white_player_id == -1 and not m.black_player_id == -1:
                    # send updated match obj
                    m = self.get_match_by_id(match_id)
                    updated_data = self.update_players(match=m)
                    return updated_data
            else:
                # todo : throw exception or smth instead of logging shit
                pass
        except Exception as e:
            logging.exception(f'[DB] Error while updating match(end):{match_id} {e}')

    def update_players(self, match: Match):
        try:
            white_pl = self.get_player_by_id(match.white_player_id)
            black_pl = self.get_player_by_id(match.black_player_id)

            white_pl.matches += 1
            black_pl.matches += 1
            white_pl.last_match_id = match.id
            black_pl.last_match_id = match.id
            white_pl.last_match_date = match.match_date
            black_pl.last_match_date = match.match_date
            res = match.result_code
            w_score = int()
            b_score = int()
            if res == "1/2-1/2":
                w_score = 0.5
                b_score = 0.5
                white_pl.draws += 1
                black_pl.draws += 1
            elif res == "1-0":
                w_score = 1
                b_score = 0
                white_pl.wins += 1
                black_pl.loses += 1
            else:
                w_score = 0
                b_score = 1
                white_pl.loses += 1
                black_pl.wins += 1

            white_pl.save(only=[Player.matches, Player.last_match_id,
                                Player.last_match_date, Player.wins,
                                Player.loses, Player.draws])
            black_pl.save(only=[Player.matches, Player.last_match_id,
                                Player.last_match_date, Player.wins,
                                Player.loses, Player.draws])

            self.update_player_elo(white_pl, black_pl, score_p1=w_score, score_p2=b_score, guild_id=match.guild_id)
            logging.info(f'[DB] Players:{white_pl.id}, {black_pl.id} has been updated')

            return {"white_player": model_to_dict(white_pl), "black_player": model_to_dict(black_pl), "match": match}
        except Exception as e:
            logging.exception(f'[DB] Error while updating players:{white_pl.id}, {black_pl.id} {e}')

    def get_player_stats(self, player_id, guild_id=None):
        try:
            pl = self.get_player_by_id(player_id)
            stats = dict()
            stats.update(player= model_to_dict(pl))
            if guild_id:
                pl_guild = self.get_guild_player_by_id(player_id=player_id, guild_id=guild_id)
                stats.update(guild_player=model_to_dict(pl_guild))
            return stats
        except Exception as e:
            logging.exception(f'[DB] Error while getting player stats:{player_id} {e}')

    # returns guild players
    def get_guild_stats(self, guild_id):
        try:
            players = self.get_guild_players_by_id(guild_id)
            return [model_to_dict(p) for p in players]
        except Exception as e:
            logging.exception(f'[DB] Error while getting guild stats:{guild_id} {e}')

    def get_player_by_id(self, player_id):
        try:
            return Player.select().where(Player.id == player_id).get()
        except:
            return None

    def get_guild_players_by_id(self, guild_id):
        try:
            players = []
            for pl in GuildPlayer.select().where(GuildPlayer.guild_id == guild_id):
                players.append(pl)
            return players
        except:
            return None

    def get_guild_player_by_id(self, guild_id, player_id):
        try:
            return GuildPlayer.select().where(GuildPlayer.player_id == player_id, GuildPlayer.guild_id == guild_id).get()
        except:
            return None

    def get_match_by_id(self, match_id):
        try:
            return Match.select().where(Match.id == match_id).get()
        except:
            return None

    def get_guild_by_id(self, guild_id):
        try:
            return Guild.select().where(Guild.id == guild_id).get()
        except:
            return None

    def get_result_code(self, match_data: dict):
        code = ""
        status = match_data['status']
        if not status == "draw":
            winner = match_data['winner']
            code = "1-0" if winner == "white" else "0-1"
        else:
            code = "1/2-1/2"
        return code

    # calculate expected score of p1 in a match against p2
    def calculate_expected_score(self, p1_elo:float, p2_elo:float):
        return 1 / (1 + 10 ** ((p1_elo - p2_elo) / 400))

    def update_player_elo(self, p1: Player, p2: Player, score_p1, score_p2, guild_id=None):
        k = ELO_CONSTANT
        try:
            # update general elo
            p1_elo = p1.elo
            p1.elo = p1.elo + k * (score_p1 - self.calculate_expected_score(p1_elo, p2.elo))
            p2.elo = p2.elo + k * (score_p2 - self.calculate_expected_score(p2.elo, p1_elo))
            # update guild elo
            if guild_id:
                p1g = self.get_guild_player_by_id(player_id=p1.id, guild_id=guild_id)
                p2g = self.get_guild_player_by_id(player_id=p2.id, guild_id=guild_id)
                p1g_elo = p1g.elo
                p1g.elo = p1g.elo + k * (score_p1 - self.calculate_expected_score(p1g_elo, p2g.elo))
                p2g.elo = p2g.elo + k * (score_p2 - self.calculate_expected_score(p2g.elo, p1g_elo))

                p1g.save(only=[GuildPlayer.elo])
                p2g.save(only=[GuildPlayer.elo])

            p1.save(only=[Player.elo])
            p2.save(only=[Player.elo])
            logging.info(f'[DB] Player elos:{p1.id}, {p2.id} has been updated')
        except Exception as e:
            logging.exception(f'[DB] Error while updating player elos:{p1.id}, {p2.id} {e}')