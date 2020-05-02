from peewee import *
import time
from logger import logging
import math

db = SqliteDatabase("db/dchess.db")

class BaseModel(Model):
    class Meta:
        database = db


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
    elo = FloatField()


class Guild(BaseModel):
    id = CharField(unique=True)


class Match(BaseModel):
    id = CharField(unique=True)
    guild_id = IntegerField()
    white_player_id = IntegerField()
    black_player_id = IntegerField()
    match_date = DateTimeField()
    result = CharField()


class DB:

    def __init__(self):
        self.connected = False
        self.init_tables()

    def init_tables(self):
        try:
            db.create_tables([Player, Match, Guild])
        except Exception as e:
            logging.exception(f"[DB] Couldn't create tables, it may already exist in db : {e})")

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
                    result=result
                )
                # logging.info(f"new match -> : {match_id}")
                return match
        except Exception as e:
            logging.exception(f'[DB] Error while adding match : {e}')

    def connect(self):
        try:
            db.connect()
            self.connected = True
        except Exception as e:
            logging.exception(f"[DB] Couldn't connect to db : {e}")

    def update_match(self, match_id, result, white_id=None, black_id=None):
        try:
            m = self.get_match_by_id(match_id)
            m.result = result
            if not white_id == None and not black_id is None:
                m.white_player_id = white_id
                m.black_player_id = black_id
            m.save(only=[Match.result, Match.white_player_id, Match.black_player_id])
            logging.info(f'[DB] Match:{match_id} has been updated')
        except Exception as e:
            logging.exception(f'[DB] Error while updating match:{match_id} {e}')

    def update_player(self, player_id, player_nick, match_id):
        try:
            p = self.get_player_by_id(player_id)
            m = self.get_match_by_id(match_id)
            p.nickname = player_nick
            p.matches += 1
            p.last_match_id = m.id
            p.last_match_date = m.match_date

            if m.result is not "unfinished":
                if m.white_player_id == player_id:
                    if m.result == "1-0":
                        p.wins += 1
                    elif m.result == "0-1":
                        p.loses += 1
                    elif m.result == "1/2-1/2":
                        p.draws += 1
                else:
                    if m.result == "1-0":
                        p.loses += 1
                    elif m.result == "0-1":
                        p.wins += 1
                    elif m.result == "1/2-1/2":
                        p.draws += 1

            m.save(only=[Player.nickname, Player.matches, Player.matches, Player.last_match_id,
                         Player.last_match_date, Player.wins, Player.loses, Player.draws])
            logging.info(f'[DB] Player:{player_id} has been updated')
        except Exception as e:
            logging.exception(f'[DB] Error while updating player:{player_id} {e}')

    def get_player_by_id(self, player_id):
        try:
           return Player.select().where(Player.id == player_id).get()
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