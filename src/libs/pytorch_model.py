from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import logging
logger = logging.getLogger()
import npy_db as ndb

class model:

    def __init__(self, ):
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        logger.debug(f"Device: {self.device}")

    def read_position_db(self, position_folder, position_file):
        positions = ndb.read_positions(position_folder, position_file)
        data = positions
        labels = positions
        self.dataT = torch.Tensor(data).to(self.device)
        self.labelsT = torch.Tensor((labels/100).reshape(len(labels), 1)).to(self.device)

    
