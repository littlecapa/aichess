import chess
import chess.pgn
import chess.engine
import logging
logger = logging.getLogger()
import cpuinfo
import platform
import re

colors = {chess.WHITE, chess.BLACK}
pieces = {chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.KING, chess.QUEEN}

MAX_EVAL = 9999

class Stockfish:

    def __init__(self, engine_path, default_eval_time = 1.0):
        logger.debug(f'Engine Path {engine_path}')
        avx2_support, popcnt_support = self.check_cpu()
        if popcnt_support:
            logger.debug(f'POPCNT Engine')
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        elif avx2_support:
            logger.debug(f'AVX2 Engine')
            self.engine = chess.engine.SimpleEngine.avx2_uci(engine_path)
        else:
            logger.error(f'No supported Engine')
            raise
        logger.debug(f'Engine loaded')
        self.set_position_from_fen()
        self.default_eval_time = default_eval_time
        return
    
    def quit(self):
        logger.debug(f'Shutdown Engine')
        self.engine.quit()

    def extract_float(self, str):
        result = re.findall(r'[-+]?\d+\.?\d*', str)[0]
        logger.debug(f'Result {result}')
        try:
            return float(result)
        except ValueError:
            logger.debug("Could not convert to float")
            return 0.0
    
    def extract_int(self, str):
        result = re.findall(r'[-+]?\d+', str)[0]
        logger.debug(f'Result {result}')
        try:
            return int(result)
        except ValueError:
            logger.debug("Could not convert to int")
            return 0
        
    def eval(self):
        if self.board.is_stalemate():
            return 0
        
        info = self.engine.analyse(self.board, chess.engine.Limit(time=self.default_eval_time))
        #logger.debug(f'Eval Info {info}')
        score = info["score"]
        if isinstance(score, chess.engine.Mate) or score.is_mate():
            if score.is_mate():
                centipawn = MAX_EVAL
            else:
                centipawn = MAX_EVAL - score.mate_score
        else:
            centipawn = score.relative.cp
        if self.board.turn == chess.BLACK:
            centipawn *= -1
        return centipawn

    def set_position_from_fen(self, fen_str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        self.board = chess.Board(fen_str)

    def set_board(self, board):
        self.board = board

    def get_board(self):
        return (self.board)
    
    def check_cpu(self):
        logger.debug(f'Architecture: {platform.architecture()}')
        info = cpuinfo.get_cpu_info()
        logger.debug(f"Flags: {info['flags']}")
        return ('avx2' in info['flags']), ('popcnt' in info['flags'])
    
    def square_index(self, square):
        square = ord(square)-ord('a')
        logger.debug(f"Square: {square}")
        return square

    def square_to_index(self, square):
        letter = chess.square_name(square)
        return 8-int(letter[1]), self.square_index[letter[0]]

    def get_bitboardstr(self):
        bit_board = []
        for color in colors:
            for piece in pieces:
                bit_board.append(self.board.pieces(piece, color))
        #logger.debug(f"Bitboards:\n{str(bit_board)}")
        return bit_board

    def get_board_infos(self):
        return self.get_bitboardstr(), self.eval()