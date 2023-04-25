import logging.config

import sys
sys.path.append('..')
from libs.engine import Stockfish

engine_path = "/usr/local/bin/stockfish"
twoknights_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"


def main():
    try:
        engine = Stockfish(engine_path)
        engine.set_position_from_fen(twoknights_fen)
        engine.eval(time_limit=1.0)
        ba = engine.get_bitboardstr()
    except:
        pass
    engine.quit()

if __name__ == '__main__':
    logging.config.fileConfig('logging.ini')
    main()
