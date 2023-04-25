import os
import numpy as np
import pandas as pd
import zstandard as zstd
import logging
logger = logging.getLogger()
import re
import chess.pgn
import io

class NpyDb:

    def __init__(self, db_path ="", db_name = "games.npy", max_games = 1000000):
        self.db_path = os.path.join(db_path, db_name)
        self.max_games = max_games
        logger.debug(f'Lichess Database Object {db_name} created')

    def __str__(self):
        return f"{self.db_path} ({self.max_games})"

    def read(self):
        try:
            self.games = np.load(self.db_path)
            logger.debug(f'Lichess Database {self.db_name} in folder {self.db_path} read, Shape: {self.games.shape}')
            return self.games
        except FileNotFoundError:
            logger.error(f'Lichess Database {self.db_name} in folder {self.b_path} not found')
        except Exception as err:
            logger.error(f'Unknown Error {err=}, {type(err)=} reading {self.db_name} in folder {self.db_path}')
        raise Exception("Database not found")

    def get_elo_frompgn(self, pgn):
        white_elo = int(pgn.headers["WhiteElo"])
        black_elo = int(pgn.headers["BlackElo"])
        return (white_elo+black_elo)/2

    def pgn2movestr(self, pgn):
        for key in list(pgn.headers.keys()):
            del pgn.headers[key]
        pgn_string = str(pgn)
        pgn_string = str(pgn).replace('\n', '').replace('  ', ' ')
        return pgn_string

    def create_from_pgnstr(self, pgn_str):
        logger.debug("Start reading PGN String")
        pgn = io.StringIO(pgn_str)
        game = chess.pgn.read_game(pgn)
        elo_list = []
        notation_list = []
        while game is not None:
            elo_list.append(self.get_elo_frompgn(game))
            notation_list.append(self.pgn2movestr(game))
            game = chess.pgn.read_game(pgn)
        # Save Notation and Elo in a dataframe
        game_df = pd.DataFrame({'notation': notation_list, 'elo': elo_list})
        # Sort the Dataframe according to strength of the players
        game_df = game_df.sort_values('elo', ascending=False)
        logger.debug(f"Shape of Database: {game_df.shape}")
        # Save the first {max_games} (according to the strength) in the Database
        np.save(self.db_path, game_df['notation'].iloc[:self.max_games])
        logger.debug("Database saved")

    def create_from_pgn(self, pgn_folder, pgn_file):
        pgn_path = os.path.join(pgn_folder, pgn_file)
        logger.debug(f"Start reading PGN File {pgn_path}")
        try:
            with open(pgn_path) as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.error(f'PGN File {self.pgn_path} not found')
        except Exception as err:
            logger.error(f'Unknown Error {err=}, {type(err)=} reading {self.pgn_path}')
        logger.debug(f"Number of lines {len(lines)}")
        pgn_string = ""
        for line in lines:
            pgn_string += line
        self.create_from_pgnstr(pgn_string)
        logger.debug("Finished reading PGN File")

    def create_from_zst(self, zst_folder, zst_file):
        zst_path = os.path.join(zst_folder, zst_file)
        logger.debug(f"Start reading ZST File {zst_path}")
        # Open the compressed file
        try:
            with open(zst_path, 'rb') as file:
                # Create a Zstandard decompressor
                dctx = zstd.ZstdDecompressor()

                # Decompress the file
                with dctx.stream_reader(file) as reader:
                    uncompressed_data = reader.read()
        except FileNotFoundError:
            logger.error(f'ZST File {self.zst_path} not found')
        except Exception as err:
            logger.error(f'Unknown Error {err=}, {type(err)=} reading {self.zst_path}')
        
        logger.debug(f'Finished reading ZST File')
        # Decode the uncompressed data
        pgn = uncompressed_data.decode('utf-8')
        self.create_from_pgnstr(pgn)
        logger.debug("Finished reading ZST File")