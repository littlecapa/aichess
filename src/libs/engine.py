import chess
import chess.pgn
import chess.engine
import logging
logger = logging.getLogger()
import cpuinfo
import platform

colors = {chess.WHITE, chess.BLACK}
pieces = {chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.KING, chess.QUEEN}

class Stockfish:

    def __init__(self, engine_path):
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
        return
    
    def quit(self):
        logger.debug(f'Shutdown Engine')
        self.engine.quit()

    def eval(self, time_limit):
        info = self.engine.analyse(self.board, chess.engine.Limit(time=time_limit))
        centipawn = int(str(info['score']).replace("PovScore(Cp(", "").replace(")", "").split(',')[0])
        logger.debug(f"Eval : {centipawn}")
        return centipawn

    def set_position_from_fen(self, fen_str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        self.board = chess.Board(fen_str)
        logger.debug(f"Position:\n{self.board}")

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
        logger.debug(f"Get Bitboard")
        bit_board = []
        for color in colors:
            for piece in pieces:
                bit_board.append(self.board.pieces(piece, color))
        logger.debug(f"Bitboards:\n{str(bit_board)}")
        return bit_board

    