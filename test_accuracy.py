import glob
import os
import sys
from sgfmill.sgfmill import sgf
import global_vars_go as gvg
import loader
import utils
import board3d as go_board
import numpy as np

kifuPath = "./kifu"
num_games = gvg.num_games
from_game = gvg.from_test_games
lb_size = 250.
correct = 0
total = 0

num_lb = int((num_games-1)/lb_size) + 1 # Number of loading batches

model = loader.load_model_from_file(gvg.nn_type)

for lb in range(num_lb):
    games = []
    print("Loading game data...")

    i = 0
    for filename in glob.glob(os.path.join(kifuPath, "*.sgf")):
        load_limit = min((lb+1) * lb_size, num_games)
        if from_game + (lb) * lb_size <= i < from_game + load_limit:
            with open(filename, "rb") as f:
                games.append(sgf.Sgf_game.from_bytes(f.read()))
        i += 1

    print("Done loading {} games".format(len(games)))

    print("Being data processing...")
    train_boards = []
    train_next_moves = []
    for game_index in range(len(games)):
        board = go_board.setup_board(games[game_index])
        for node in games[game_index].get_main_sequence():
            board = go_board.switch_player_perspec(board) # Changes player perspective, black becomes white and vice versa

            node_move = node.get_move()[1]
            if node_move is not None:
                train_boards.append(go_board.get_encoded_board(board))
                next_move = np.zeros(gvg.board_size * gvg.board_size).reshape(gvg.board_size, gvg.board_size)
                next_move[node_move[0], node_move[1]] = gvg.filled # y = an array in the form [board_x_position, board_y_position]
                train_next_moves.append(next_move.reshape(gvg.board_size * gvg.board_size))

                board = go_board.make_move(board, node_move, gvg.bot_channel, gvg.player_channel) # Update board with new move
                if board is None:
                    print("ERROR! Illegal move, {}, while training".format(node_move))
    print("Finished data processing...")

    print("Begin testing...")
    for i in range(len(train_boards)):
        pred = np.asarray(model.predict(train_boards[i].reshape(1, gvg.board_size, gvg.board_size, gvg.enc_board_channels))) \
        .reshape(gvg.board_size * gvg.board_size)
        if pred.argmax() == train_next_moves[i].argmax():
            correct += 1
        total += 1
print("Accuracy: {}".format(correct/total))
print("Finished testing")
