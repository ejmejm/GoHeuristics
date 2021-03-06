import numpy as np
import queue
import time
import global_vars_go as gvg
from sgfmill.sgfmill import sgf_moves

empty = gvg.empty
filled = gvg.filled
color_to_play = gvg.kgs_black # Used to track stone color for KGS Engine

prev_moves = [[-10, -10], [-10, -10], [-10, -10], [-10, -10]]

prev_boards = [np.zeros((gvg.board_size, gvg.board_size, gvg.board_channels)), \
              np.zeros((gvg.board_size, gvg.board_size, gvg.board_channels))] # Keep track of previous board to avoid Ko violation

last_liberties = np.zeros((gvg.board_size, gvg.board_size, 4))

true_liberties = np.zeros((gvg.board_size, gvg.board_size))

prev_liberties = [np.zeros((gvg.board_size, gvg.board_size, 4)), \
              np.zeros((gvg.board_size, gvg.board_size, 4))]

def reset_liberties():
    last_liberties = np.zeros((gvg.board_size, gvg.board_size, 4))
    prev_liberties = [np.zeros((gvg.board_size, gvg.board_size, 4)), \
                  np.zeros((gvg.board_size, gvg.board_size, 4))]

def make_move(board, move, player, enemy, debug=False, result_only=False):
    global last_liberties

    if board[move[0]][move[1]][player] == filled or board[move[0]][move[1]][enemy] == filled: # Return false if illegal move
        print("ERROR! Tried to make illegal move at ({},{}) where there is already a piece".format(move[0], move[1]))
        return False

    board = board.reshape(gvg.board_size, gvg.board_size, gvg.board_channels)
    backup_board = np.empty_like(prev_boards[1])
    backup_board[:] = prev_boards[1]
    backup_liberty = np.empty_like(prev_liberties[1])
    backup_liberty[:] = prev_liberties[1]
    prev_boards[1][:] = prev_boards[0] # Update previous board to the current board
    prev_boards[0][:] = board
    prev_liberties[1][:] = prev_liberties[0] # Update previous liberties to the current liberties
    prev_liberties[0][:] = last_liberties

    board[move[0]][move[1]][player] = filled

    liberty_updated = np.zeros((gvg.board_size, gvg.board_size)) # If a stone has already had its liberties updated

    update_marked = []

    group_captures = 0
    if move[0] + 1 <= 18:
        if liberty_updated[move[0]+1, move[1]] == 0 and board[move[0]+1][move[1]][enemy] == filled:
            if check_liberties(board, np.array([move[0]+1, move[1]])) - 1 == 0:
                _, ul = remove_stones(board, np.array([move[0]+1, move[1]]), mark_updates=True)
                update_marked += ul
                group_captures += 1
            else:
                update_marked.append((move[0]+1, move[1]))
    if move[0] - 1 >= 0:
        if liberty_updated[move[0]-1, move[1]] == 0 and board[move[0]-1][move[1]][enemy] == filled:
            if check_liberties(board, np.array([move[0]-1, move[1]])) - 1 == 0:
                _, ul = remove_stones(board, np.array([move[0]-1, move[1]]), mark_updates=True)
                update_marked += ul
                group_captures += 1
            else:
                update_marked.append((move[0]-1, move[1]))
    if move[1] + 1 <= 18:
        if liberty_updated[move[0], move[1]+1] == 0 and board[move[0]][move[1]+1][enemy] == filled:
            if check_liberties(board, np.array([move[0], move[1]+1])) - 1 == 0:
                _, ul = remove_stones(board, np.array([move[0], move[1]+1]), mark_updates=True)
                update_marked += ul
                group_captures += 1
            else:
                update_marked.append((move[0], move[1]+1))
    if move[1] - 1 >= 0:
        if liberty_updated[move[0], move[1]-1] == 0 and board[move[0]][move[1]-1][enemy] == filled:
            if check_liberties(board, np.array([move[0], move[1]-1])) - 1 == 0:
                _, ul = remove_stones(board, np.array([move[0], move[1]-1]), mark_updates=True)
                update_marked += ul
                group_captures += 1
            else:
                update_marked.append((move[0], move[1]-1))

    # Update liberties for who played the move
    update_liberty_group(board, (move[0], move[1]), updated_map=liberty_updated)

    for m in update_marked:
        update_liberty_group(board, m, updated_map=liberty_updated)

    if legal_move(board, move, player=player, debug=True) == False: # If the move made is illegal
        board[:] = prev_boards[0] # Undo it
        prev_boards[0][:] = prev_boards[1]
        prev_boards[1][:] = backup_board
        last_liberties[:] = prev_liberties[0]
        prev_liberties[0][:] = prev_liberties[1]
        prev_liberties[1][:] = backup_liberty
        return False

    if result_only == True:
        board[:] = prev_boards[0] # Undo it
        prev_boards[0][:] = prev_boards[1]
        prev_boards[1][:] = backup_board
        last_liberties[:] = prev_liberties[0]
        prev_liberties[0][:] = prev_liberties[1]
        prev_liberties[1][:] = backup_liberty
        return True

    prev_moves[3] = prev_moves[2]
    prev_moves[2] = prev_moves[1]
    prev_moves[1] = prev_moves[0]
    prev_moves[0] = move

    return board

def legal_move(board, move, player=None, debug=False): # If it is legal to make a move in a space
    # If the player whose made the move has not been given, find who it was (assumes move has already been made)
    if player is None:
        if board[move[0]][move[1]][gvg.bot_channel] == gvg.filled:
            player = gvg.bot_channel
            enemy = gvg.player_channel
        elif board[move[0]][move[1]][gvg.player_channel] == gvg.filled:
            player = gvg.player_channel
            enemy = gvg.bot_channel
        else:
            if debug == True:
                print("ERROR! Cannot check for (il)legal move at empty space, (", move[0]+1, ", ", move[1]+1, ")")
            return 0
    else:
        if player == gvg.bot_channel:
            enemy = gvg.player_channel
        else:
            enemy = gvg.bot_channel

    if check_liberties(board, move) == 0:
        if debug == True:
            print("ERROR! Illegal suicide move")
        return False
    elif (board == prev_boards[1]).all(): # If Ko
        if debug == True:
            print("ERROR! Illegal Ko violation")
        return False

    return True

def check_captures(orig_board, move, debug=False, lib_offset=0):
    board = np.copy(orig_board)

    if board[move[0]][move[1]][gvg.bot_channel] == gvg.filled:
        player = gvg.bot_channel
        enemy = gvg.player_channel
    elif board[move[0]][move[1]][gvg.player_channel] == gvg.filled:
        player = gvg.player_channel
        enemy = gvg.bot_channel
    else:
        if debug == True:
            print("ERROR! Cannot check the captures of an empty space at, (", move[0]+1, ", ", move[1]+1, ")")
        return 0

    captures = 0
    if move[0] + 1 <= 18 and board[move[0]+1][move[1]][enemy] == filled and check_liberties(board, np.array([move[0]+1, move[1]]))-lib_offset == 0:
        captures += remove_stones(board, np.array([move[0]+1, move[1]]))
    if move[0] - 1 >= 0 and board[move[0]-1][move[1]][enemy] == filled and check_liberties(board, np.array([move[0]-1, move[1]]))-lib_offset == 0:
        captures += remove_stones(board, np.array([move[0]-1, move[1]]))
    if move[1] + 1 <= 18 and board[move[0]][move[1]+1][enemy] == filled and check_liberties(board, np.array([move[0], move[1]+1]))-lib_offset == 0:
        captures += remove_stones(board, np.array([move[0], move[1]+1]))
    if move[1] - 1 >= 0 and board[move[0]][move[1]-1][enemy] == filled and check_liberties(board, np.array([move[0], move[1]-1]))-lib_offset == 0:
        captures += remove_stones(board, np.array([move[0], move[1]-1]))

    return captures

def set_liberty(move, val):
    true_liberties[move[0], move[1]] = val
    last_liberties[move[0], move[1], 0] = gvg.empty
    last_liberties[move[0], move[1], 1] = gvg.empty
    last_liberties[move[0], move[1], 2] = gvg.empty
    last_liberties[move[0], move[1], 3] = gvg.empty
    val = min(val, 4)
    if val > 0:
        last_liberties[move[0], move[1], val - 1] = gvg.filled

def get_liberty(position):
    if last_liberties[position[0], position[1], 0] == gvg.filled:
        return 1
    elif last_liberties[position[0], position[1], 1] == gvg.filled:
        return 2
    elif last_liberties[position[0], position[1], 2] == gvg.filled:
        return 3
    elif last_liberties[position[0], position[1], 3] == gvg.filled:
        return 4
    else:
        return 0

def update_liberty_group(board, position, updated_map=None, debug=False):

    if updated_map[position[0], position[1]] != 0: # If this point has already been checked, don't check it again
        return;

    if board[position[0]][position[1]][gvg.bot_channel] == gvg.filled:
        player = gvg.bot_channel
        enemy = gvg.player_channel
    elif board[position[0]][position[1]][gvg.player_channel] == gvg.filled:
        player = gvg.player_channel
        enemy = gvg.bot_channel
    else:
        set_liberty(move, 0)
        return;

    if updated_map is None:
        updated_map = np.zeros(gvg.board_size, gvg.board_size)

    positions = queue.Queue()
    positions.put(position)
    updated_map[position[0], position[1]] = -1 # -1 for final liberty needs to be set, 1 for no futher update needed

    liberties = 0
    while positions.empty() == False:
        c_move = positions.get()
        if c_move[0] + 1 <= 18 and updated_map[c_move[0]+1, c_move[1]] == 0:
            if board[c_move[0]+1][c_move[1]][player] == filled:
                positions.put(np.array([c_move[0]+1, c_move[1]]))
                updated_map[c_move[0]+1, c_move[1]] = -1
            elif board[c_move[0]+1][c_move[1]][enemy] == empty:
                liberties += 1
                updated_map[c_move[0]+1, c_move[1]] = 1
            else:
                updated_map[c_move[0]+1, c_move[1]] = 1
        if c_move[0] - 1 >= 0 and updated_map[c_move[0]-1, c_move[1]] == 0:
            if board[c_move[0]-1][c_move[1]][player] == filled:
                positions.put(np.array([c_move[0]-1, c_move[1]]))
                updated_map[c_move[0]-1, c_move[1]] = -1
            elif board[c_move[0]-1][c_move[1]][enemy] == empty:
                liberties += 1
                updated_map[c_move[0]-1, c_move[1]] = 1
            else:
                updated_map[c_move[0]-1, c_move[1]] = 1
        if c_move[1] + 1 <= 18 and updated_map[c_move[0], c_move[1]+1] == 0:
            if board[c_move[0]][c_move[1]+1][player] == filled:
                positions.put(np.array([c_move[0], c_move[1]+1]))
                updated_map[c_move[0], c_move[1]+1] = -1
            elif board[c_move[0]][c_move[1]+1][enemy] == empty:
                liberties += 1
                updated_map[c_move[0], c_move[1]+1] = 1
            else:
                updated_map[c_move[0], c_move[1]+1] = 1
        if c_move[1] - 1 >= 0 and updated_map[c_move[0], c_move[1]-1] == 0:
            if board[c_move[0]][c_move[1]-1][player] == filled:
                positions.put(np.array([c_move[0], c_move[1]-1]))
                updated_map[c_move[0], c_move[1]-1] = -1
            elif board[c_move[0]][c_move[1]-1][enemy] == empty:
                liberties += 1
                updated_map[c_move[0], c_move[1]-1] = 1
            else:
                updated_map[c_move[0], c_move[1]-1] = 1

    for i in range(updated_map.shape[0]):
        for j in range(updated_map.shape[1]):
            if updated_map[i][j] == -1:
                set_liberty((i, j), liberties);
                updated_map[i][j] = 1
            else:
                updated_map[i][j] = 0

    return liberties

def check_liberties(board, position, debug=False):
    return get_liberty(position)

def remove_stones(board, position, count_only=False, mark_updates=False, lib_offset=0):
    board = board.reshape(gvg.board_size, gvg.board_size, gvg.board_channels)
    if board[position[0]][position[1]][gvg.bot_channel] == filled:
        player = gvg.bot_channel
        enemy = gvg.player_channel
    elif board[position[0]][position[1]][gvg.player_channel] == filled:
        player = gvg.player_channel
        enemy = gvg.bot_channel
    else:
        print("ERROR! Cannot remove stones at the empty spot, (", move[0]+1, ", ", move[1]+1, ")")
        return;

    if mark_updates:
        update_list = []
    board_check = np.empty((gvg.board_size, gvg.board_size))
    captures = 0
    board_check.fill(False)
    positions = queue.Queue()
    positions.put(position)
    board_check[position[0]][position[1]] = True

    while positions.empty() == False:
        c_move = positions.get() # Get newest move in queue
        if c_move[0] + 1 <= 18 and board_check[c_move[0]+1][c_move[1]] == False: # If a surrounding stone is within bounds and has yet to be queued
            if board[c_move[0]+1][c_move[1]][player] == filled: # If it's a move by us
                positions.put(np.array([c_move[0]+1, c_move[1]])) # Put it in the queue to check and delete
            elif mark_updates and board[c_move[0]+1][c_move[1]][enemy] == filled: # If it's an opponent's move
                update_list.append((c_move[0]+1, c_move[1])) # Add to list of liberties to be updated later
            board_check[c_move[0]+1][c_move[1]] = True  # Mark it as added to the queue
        if c_move[0] - 1 >= 0 and board_check[c_move[0]-1][c_move[1]] == False:
            if board[c_move[0]-1][c_move[1]][player] == filled:
                positions.put(np.array([c_move[0]-1, c_move[1]]))
            elif mark_updates and board[c_move[0]-1][c_move[1]][enemy] == filled:
                update_list.append((c_move[0]-1, c_move[1]))
            board_check[c_move[0]-1][c_move[1]] = True
        if c_move[1] + 1 <= 18 and board_check[c_move[0]][c_move[1]+1] == False:
            if board[c_move[0]][c_move[1]+1][player] == filled:
                positions.put(np.array([c_move[0], c_move[1]+1]))
            elif mark_updates and board[c_move[0]][c_move[1]+1][enemy] == filled:
                update_list.append((c_move[0], c_move[1]+1))
            board_check[c_move[0]][c_move[1]+1] = True
        if c_move[1] - 1 >= 0 and board_check[c_move[0]][c_move[1]-1] == False:
            if board[c_move[0]][c_move[1]-1][player] == filled:
                positions.put(np.array([c_move[0], c_move[1]-1]))
            elif mark_updates and board[c_move[0]][c_move[1]-1][enemy] == filled:
                update_list.append((c_move[0], c_move[1]-1))
            board_check[c_move[0]][c_move[1]-1] = True
        if count_only == False: # If we want to actually remove stones
            board[c_move[0]][c_move[1]][player] = empty # Remove the stone
            set_liberty(c_move, 0) # Set it to 0 liberties
        captures += 1 # Add 1 to our capture count

    if mark_updates:
        return captures, update_list

    return captures

def encode_liberty_channels(board):
    liberty_channels = np.zeros((8, gvg.board_size, gvg.board_size))
    for i in range(gvg.board_size):
        for j in range(gvg.board_size):
            if board[i, j, gvg.bot_channel] == filled:
                liberties = min(check_liberties(board, (i, j), True), 4)
                liberty_channels[liberties - 1, i, j] = gvg.filled
            elif board[i, j, gvg.player_channel] == filled:
                liberties = min(check_liberties(board, (i, j), True), 4)
                liberty_channels[liberties + 3, i, j] = gvg.filled
    return liberty_channels

def encode_capture_channels(board):
    capture_channels = np.zeros((8, gvg.board_size, gvg.board_size))
    for i in range(gvg.board_size):
        for j in range(gvg.board_size):
            if board[i, j, gvg.bot_channel] == empty and \
                board[i, j, gvg.player_channel] == empty:

                board[i, j, gvg.bot_channel] = filled
                captures = min(check_captures(board, (i, j)), 4)
                board[i, j, gvg.bot_channel] = empty
                if captures > 0:
                    capture_channels[captures-1, i, j] = filled

                board[i, j, gvg.player_channel] = filled
                captures = min(check_captures(board, (i, j)), 4)
                board[i, j, gvg.player_channel] = empty
                if captures > 0:
                  capture_channels[captures + 3, i, j] = filled

    return capture_channels

def encode_border_channel(board):
    return np.ones((gvg.board_size, gvg.board_size))

def encode_empty_channel(board):
    empty_channel = np.zeros((gvg.board_size, gvg.board_size))
    for i in range(gvg.board_size):
        for j in range(gvg.board_size):
            if board[i, j, gvg.bot_channel] == empty and \
                board[i, j, gvg.player_channel] == empty:
                empty_channel[i, j] = filled

    return empty_channel

def encode_prev_moves_channels(board):
    prev_moves_channels = np.zeros((4, gvg.board_size, gvg.board_size))

    for i in range(4):
        if prev_moves[i][0] >= 0 and prev_moves[i][1] >= 0:
            prev_moves_channels[i, prev_moves[0], prev_moves[1]] = filled

    return prev_moves_channels

# Takes ~20 milliseconds on average
def get_encoded_board(board):
    enc_board = np.zeros((gvg.board_size, gvg.board_size, 20))
    for i in range(enc_board.shape[0]):
        for j in range(enc_board.shape[1]):
            # Border channel
            enc_board[i, j, gvg.border_channel] = filled
            if board[i, j, gvg.bot_channel] == filled:
                enc_board[i, j, gvg.bot_channel] = filled

                # Liberties
                liberties = min(check_liberties(board, (i, j)), 4)
                if liberties > 0:
                    enc_board[i, j, gvg.bot_liberty_channels[0] + liberties - 1] = filled
            elif board[i, j, gvg.player_channel] == filled:
                enc_board[i, j, gvg.player_channel] = filled

                # Liberties
                liberties = min(check_liberties(board, (i, j)), 4)
                if liberties > 0:
                    enc_board[i, j, gvg.player_liberty_channels[0] + liberties - 1] = filled
            else:
                enc_board[i, j, gvg.empty_channel] = filled

    for i in range(enc_board.shape[0]):
        for j in range(enc_board.shape[1]):
            if enc_board[i, j, gvg.empty_channel] == filled:
                board[i, j, gvg.bot_channel] = filled
                enemy = gvg.player_channel

                # Captures channel
                captures = 0

                if i+1 <= 18 and board[i+1, j, enemy] == filled and \
                enc_board[i+1, j, gvg.player_liberty_channels[1]] == 0 and \
                enc_board[i+1, j, gvg.player_liberty_channels[2]] == 0 and \
                enc_board[i+1, j, gvg.player_liberty_channels[3]] == 0:
                    captures = min(captures + remove_stones(board, np.array([i+1, j]), count_only=True), 4)
                if captures < 4 and i-1 >= 0 and board[i-1, j, enemy] == filled and \
                enc_board[i-1, j, gvg.player_liberty_channels[1]] == 0 and \
                enc_board[i-1, j, gvg.player_liberty_channels[2]] == 0 and \
                enc_board[i-1, j, gvg.player_liberty_channels[3]] == 0:
                    captures = min(captures + remove_stones(board, np.array([i-1, j]), count_only=True), 4)
                if captures < 4 and j+1 <= 18 and board[i, j+1, enemy] == filled and \
                enc_board[i, j+1, gvg.player_liberty_channels[1]] == 0 and \
                enc_board[i, j+1, gvg.player_liberty_channels[2]] == 0 and \
                enc_board[i, j+1, gvg.player_liberty_channels[3]] == 0:
                    captures = min(captures + remove_stones(board, np.array([i, j+1]), count_only=True), 4)
                if captures < 4 and j-1 >= 0 and board[i, j-1, enemy] == filled and \
                enc_board[i, j-1, gvg.player_liberty_channels[1]] == 0 and \
                enc_board[i, j-1, gvg.player_liberty_channels[2]] == 0 and \
                enc_board[i, j-1, gvg.player_liberty_channels[3]] == 0:
                    captures = min(captures + remove_stones(board, np.array([i, j-1]), count_only=True), 4)

                board[i, j, gvg.bot_channel] = empty

                if captures > 0:
                    enc_board[i, j, gvg.capture_channels[0] + captures - 1] = filled

    # Prev moves
    for i in range(4):
        if prev_moves[i][0] >= 0 and prev_moves[i][1] >= 0:
            enc_board[prev_moves[i][0], prev_moves[i][1], gvg.prev_moves_channels[i]] = filled

    return enc_board

def switch_player_perspec(board):
    board = board.reshape(gvg.board_size, gvg.board_size, gvg.board_channels)
    for i in range(len(board)):
        for j in range(len(board[i])):
            tmp = board[i][j][gvg.player_channel]
            board[i][j][gvg.player_channel] = board[i][j][gvg.bot_channel]
            board[i][j][gvg.bot_channel] = tmp
    tmp = gvg.black_channel
    gvg.black_channel = gvg.white_channel
    gvg.white_channel = tmp

    return board

def setup_board(game):
    #color_to_play = gvg.kgs_black
    #Switch which color is which channel when the channels are switched
    reset_liberties()
    bc = gvg.black_channel
    gvg.black_channel = gvg.white_channel
    gvg.white_channel = bc
    preboard, plays = sgf_moves.get_setup_and_moves(game)
    rpreboard = preboard.board
    board = np.zeros((gvg.board_size, gvg.board_size, gvg.board_channels))
    if len(plays) < 1: # Return an empty board if the game has no moves
        return board
    if plays[0][0] == "b":
        color_stone = gvg.bot_channel
    else:
        color_stone = gvg.player_channel
    for i in range(len(rpreboard)):
        for j in range(len(rpreboard[i])):
            if rpreboard[i][j] == "b":
                board[i][j][color_stone] = gvg.filled
                set_liberty((i, j), 4)

    return board.astype(int)

def empty_board(color): # Color is the bot's color
    color_to_play = color
    reset_liberties()
    prev_boards = [np.zeros((gvg.board_size, gvg.board_size, gvg.board_channels)), \
                  np.zeros((gvg.board_size, gvg.board_size, gvg.board_channels))]
    return np.zeros((gvg.board_size, gvg.board_size, gvg.board_channels))

def set_color(color):
    if color_to_play is None:
        color_to_play = color

# Prints ASCII representation of the board
def show_board(board):
    for i in range(board.shape[0]):
        print()
        for j in range(board.shape[1]):
            if(board[j, gvg.board_size-1-i, gvg.black_channel] == gvg.filled):
                print("X ", end='')
            elif(board[j, gvg.board_size-1-i, gvg.white_channel] == gvg.filled):
                print("O ", end='')
            else:
                print(". ", end='')
    print("-------------------------------------")
    show_liberties()

# Returns string representation of the board
def board_to_str(board):
    vis = ""
    for i in range(board.shape[0]):
        vis += "\n"
        for j in range(board.shape[1]):
            if(board[j, gvg.board_size-1-i, gvg.black_channel] == gvg.filled):
                vis += "X "
            elif(board[j, gvg.board_size-1-i, gvg.white_channel] == gvg.filled):
                vis += "O "
            else:
                vis += ". "
    return vis + "\n-------------------------------------\n" + liberties_to_str()

# Prints ASCII representation of the liberties
def show_liberties():
    for i in range(last_liberties.shape[0]):
        print()
        for j in range(last_liberties.shape[1]):
            if(last_liberties[j, gvg.board_size-1-i, 0] == gvg.filled):
                print("1 ", end='')
            elif(last_liberties[j, gvg.board_size-1-i, 1] == gvg.filled):
                print("2 ", end='')
            elif(last_liberties[j, gvg.board_size-1-i, 2] == gvg.filled):
                print("3 ", end='')
            elif(last_liberties[j, gvg.board_size-1-i, 3] == gvg.filled):
                print("4 ", end='')
            else:
                print(". ", end='')

# Returns string representation of the liberties
def liberties_to_str():
    vis = ""
    for i in range(last_liberties.shape[0]):
        vis += "\n"
        for j in range(last_liberties.shape[1]):
            lib = get_liberty((j, gvg.board_size-1-i))
            if lib == 0:
                vis += ". "
            else:
                vis += str(lib) + " "
    return vis
