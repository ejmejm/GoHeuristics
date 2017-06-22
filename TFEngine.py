import numpy as np
import random
import os
from Engine import *
from GTP import Move
import go_nn as go_learn
import board3d as go_board

# def softmax(E, temp):
#     #print "E =\n", E
#     expE = np.exp(temp * (E - max(E))) # subtract max to avoid overflow
#     return expE / np.sum(expE)
#
# def sample_from(probs):
#     cumsum = np.cumsum(probs)
#     r = random.random()
#     for i in xrange(len(probs)):
#         if r <= cumsum[i]:
#             return i
#     assert False, "problem with sample_from"


class TFEngine(BaseEngine):
    def __init__(self, eng_name, model):
        super(TFEngine,self).__init__()
        self.eng_name = eng_name
        self.model = model

        self.last_move_probs = np.zeros((gvg.board_size, gvg.board_size,))
        self.kibitz_mode = False

    def name(self):
        return self.eng_name

    def version(self):
        return "1.0"

    def set_board_size(self, N):
        if N != gvg.board_size:
            return False
        return BaseEngine.set_board_size(self, N)

    # def pick_book_move(self, color):
    #     if self.book:
    #         book_move = Book.get_book_move(self.board, self.book)
    #         if book_move:
    #             print "playing book move", book_move
    #             return Move(book_move[0], book_move[1])
    #         print "no book move"
    #     else:
    #         print "no book"
    #     return None

    def pick_model_move(self, color):
        if color != gvg.kgs_black:
            self.board = go_board.switch_player_perspec(self.board)
        prob_board = np.array(self.model.predict(self.board.reshape(-1, gvg.board_size, gvg.board_size, gvg.board_channels))).reshape((gvg.board_size, gvg.board_size))
        self.last_move_probs = prob_board

        move = []
        found_move = False
        while found_move == False:
            move = go_learn.nanargmax(prob_board)
            if self.board[move[0]][move[1]][gvg.player_channel] == gvg.filled or self.board[move[0]][move[1]][gvg.bot_channel] == gvg.filled:
                prob_board[move[0]][move[1]] = -999999.0
            else:
                found_move = True

        return Move(move[0], move[1])

    def pick_move(self, color):
        # book_move = self.pick_book_move(color)
        # if book_move:
        #     if self.kibitz_mode: # in kibitz mode compute model probabilities anyway
        #         self.pick_model_move(color) # ignore the model move
        #     return book_move
        return self.pick_model_move(color)

    def get_last_move_probs(self):
        return self.last_move_probs

    def stone_played(self, x, y, color):
        # if we are in kibitz mode, we want to compute model probabilities for ALL turns
        # if self.kibitz_mode:
        #     self.pick_model_move(color)
        #     true_stderr.write("probability of played move %s (%d, %d) was %.2f%%\n" % (color_names[color], x, y, 100*self.last_move_probs[x,y]))

        BaseEngine.stone_played(self, x, y, color)

    def toggle_kibitz_mode(self):
        self.kibitz_mode = ~self.kibitz_mode
        return self.kibitz_mode