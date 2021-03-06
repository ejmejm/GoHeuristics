import sys
import argparse

empty = 0 # Board integer for empty spaces
filled = 1 # Board integer for filled spaces
bot_channel = 0 # Board channel used for bot moves
player_channel = 1 # Board channel used for bot moves
empty_channel = 2 # Channel for empty board positions
bot_liberty_channels = [3, 4, 5, 6] # Channels for liberties of bot
player_liberty_channels = [7, 8, 9, 10] # Channels for liberties of oppenent
capture_channels = [11, 12, 13, 14] # Channels for the captures of the bot
prev_moves_channels = [15, 16, 17, 18] # Channels for previous moves made
border_channel = 19 # Channel to keep clear border when padding
enc_board_channels = 20
num_games = 1000 # Number of games to train and test accuracy on
hm_epochs = 7 # Number of loops through all training data
process_batch_size = 64 * 500 # Number of games to process into board states before fitting
train_batch_size = 64 # Number of board states to send to the GPU at once
train_display_stride = 30 # Number of batches before giving a visual update
file_load_split = 5000 # Number of games to load from disk to RAM at once
nn_type = "ejmodel" # Which model to use for training and testing
validation_split = 0.03 # What fraction of games are reserved for validation
from_test_games = 100000 # How many games are reserved for training/where testing starts
learning_rate = 0.001 # Learning rate for training
board_size = 19 # Side length of the Go board
board_channels = 2 # 3rd dimmension of the board
checkpoint_path = "checkpoints/" # Where model checkpoints are stored
cont_from_save = "false" # True if loading a model save from a checkpoint and False otherwise
kgs_empty = 0 # Empty with KGS engine
kgs_black = 1 # Black stone with KGS engine
kgs_white = 2 # White stone with KGS engine
black_channel = bot_channel # Black stone with KGS engine
white_channel = player_channel # White stone with KGS engine
load_split_offset = 0 # Offset on which split to start training at

# Soon to be depricated
empty_in = 0 # Board integer for empty spaces
bot_in = 1 # Board integer for spaces occupied by the bot
player_in = 2 # Board integer for spaces occupied by the player

parser = argparse.ArgumentParser(description="EJGo flag parser")

parser.add_argument('-n', "--num_games", action="store", dest="num_games", type=int, default=1000)
parser.add_argument('-m', "--model", action="store", dest="nn_type", type=str, default="ejmodel")
parser.add_argument('-s', "--use_save", action="store", dest="cont_from_save", type=str, default="false")
parser.add_argument('-o', "--offset", action="store", dest="load_split_offset", type=int, default=0)
args = parser.parse_args()

num_games = args.num_games
nn_type = args.nn_type
cont_from_save = args.cont_from_save
load_split_offset = args.load_split_offset

# if len(sys.argv) >= 2:
#     num_games = int(sys.argv[1])
# if len(sys.argv) >= 3:
# 	nn_type = sys.argv[2]
# if len(sys.argv) >= 4:
# 	cont_from_save = sys.argv[3]
# if len(sys.argv) >= 5:
# 	load_split_offset = int(sys.argv[4])
