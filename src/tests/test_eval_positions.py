import logging.config

import sys
sys.path.append('..')
from libs.npy_db import NpyDb as ndb

def main():
    db = ndb()
    positions = db.read_all_positions(True)
    db.write_position_db(positions, "", "pos_eavl.npy")

if __name__ == '__main__':
    logging.config.fileConfig('logging.ini')
    main()
