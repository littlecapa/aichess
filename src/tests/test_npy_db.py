import logging.config

import sys
sys.path.append('..')
from libs.npy_db import NpyDb as ndb

zst_folder = "/Users/littlecapa/Downloads"
zst_file = "archive.zst"

pgn_file = "lichess_Badchess64_2023-04-24.pgn"


def main():
    db = ndb()
    db.create_from_zst(zst_folder, zst_file)
    db.create_from_pgn(zst_folder, pgn_file)


if __name__ == '__main__':
    logging.config.fileConfig('logging.ini')
    main()
