import os
import numpy as np
import pandas as pd
import zstandard as zstd
import logging
logger = logging.getLogger()
import re
import chess.pgn
import io
from libs.engine import Stockfish

class NpyDb:

    def __init__(self, db_path ="", db_name = "games.npy", max_games = 1000000, engine_path = "/usr/local/bin/stockfish"):
        self.db_path = os.path.join(db_path, db_name)
        self.max_games = max_games
        self.engine_path = engine_path
        logger.debug(f'Lichess Database Object {db_name} created')

    def __str__(self):
        return f"{self.db_path} ({self.max_games})"

    def read(self):
        try:
            self.games = np.load(self.db_path, allow_pickle=True)
            logger.debug(f'Lichess Database {self.db_path} read, Shape: {self.games.shape}')
            return self.games
        except FileNotFoundError:
            logger.error(f'Lichess Database {self.db_path} not found')
        except Exception as err:
            logger.error(f'Unknown Error {err=}, {type(err)=} reading {self.db_path}')
        raise Exception("Database not found")
    
    def game2positions(self, game_nr, pgn, engine, annotated):
        logger.debug(f"Start Reading all Positions in game {game_nr}")
        game = chess.pgn.read_game(io.StringIO(pgn))
        boards = []
        bitboards = []
        evals = []
        board = game.board()
        half_moves = []
        half_move = 1
        for move in game.mainline_moves():
            board.push(move)
            boards.append(board)
            half_moves.append(half_move)
            if annotated:
                engine.set_board(board)
                bitboard, eval = engine.get_board_infos()
                bitboards.append(bitboard)
                evals.append(eval)
            half_move += 1
        if annotated:
            data = {'HalfMove': half_moves, 'Board': boards, 'Bitboard': bitboards, 'Eval': evals}
        else:
            data = {'HalfMove': half_moves, 'Board': boards}
        game_positions = pd.DataFrame(data)
        game_positions["GameNr"] = game_nr
        return game_positions

    def read_all_positions(self, annotated = False):
        logger.debug("Start Reading all Positions")
        games = self.read()
        engine = Stockfish(self.engine_path, 1.0)
        board = engine.get_board()
        try:
            for game_nr, game in enumerate(games):
                logger.debug(f"Processing Game: {game_nr}")
                new_positions = self.game2positions(game_nr, game, engine, annotated)
                if game_nr == 0:
                    positions = new_positions
                else:
                    positions = pd.concat([positions, new_positions])
        except Exception as err:
            logger.error(f'Unknown Error {err=}, {type(err)=} reading all positions')
            positions = []
        engine.quit()
        logger.debug(f"Position Head: \n{positions.head()}")
        logger.debug(f"Position Tail: \n{positions.tail()}")
        logger.debug(f"Position Shape: \n{positions.shape}")
        logger.debug(f"Position Transition: \n{positions.T}")
        return positions

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

    def read_position_db(self, position_folder, position_file):
        position_path = os.path.join(position_folder, position_file)
        try:
            self.positions = np.load(position_path)
            logger.debug(f'Position Database {position_path} read, Shape: {self.positions.shape}')
            return self.positions
        except FileNotFoundError:
            logger.error(f'Position Database {position_path} not found')
        except Exception as err:
            logger.error(f'Unknown Error {err=}, {type(err)=} reading Position Database {position_path}')
        raise Exception("Database not found")
    
    def write_position_db(self, positions, position_folder, position_file):
        position_path = os.path.join(position_folder, position_file)
        np.save(position_path, positions)
        logger.debug("Database saved")
