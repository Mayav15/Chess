# Chess AI — Board logic and minimax AI with alpha-beta pruning

import random

FILE_LETTERS = 'abcdefgh'
#The letters used in chess notation, a-h representing the columns (files) of the board

# How much each piece is worth, used by the AI to evaluate board positions
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables tell the AI which squares are better for each piece type
# Each table has 64 values (8x8 board), with higher numbers meaning that square is more desirable
# For example, pawns are worth more when pushed forward, knights are worth more in the center
PIECE_SQUARE_TABLES = {
    'P': [ 0, 0, 0, 0, 0, 0, 0, 0, 50,50,50,50,50,50,50,50,
          10,10,20,30,30,20,10,10,  5, 5,10,25,25,10, 5, 5,
           0, 0, 0,20,20, 0, 0, 0,  5,-5,-10,0, 0,-10,-5,5,
           5,10,10,-20,-20,10,10,5, 0, 0, 0, 0, 0, 0, 0, 0],
    'N': [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,
          -30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,
          -30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,
          -40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50],
    'B': [-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,
          -10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,
          -10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,
          -10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20],
    'R': [ 0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5,
          -5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,
          -5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,
          -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0],
    'Q': [-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,
          -10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,
           0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,
          -10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20],
    'K': [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,
          -20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,
           20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20],
}

AI_DEPTH = 3
#Default search depth for the AI. Higher depth = smarter AI but slower


# Board logic and move generation
class ChessBoard:
    #This class handles all the chess rules: creating the board, generating legal moves,
    #checking for check/checkmate, applying moves, and handling special moves like castling and en passant

    def __init__(self):
        self.board = self.create_board()

    def create_board(self):
        #Sets up the starting chess position with all pieces in their correct places
        back_row = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        board = [[None] * 8 for _ in range(8)]
        #8x8 grid, None means empty square

        for col, piece in enumerate(back_row):
            board[0][col] = (piece, 'b')  #Row 0 is black's back rank
            board[7][col] = (piece, 'w')  #Row 7 is white's back rank
        for col in range(8):
            board[1][col] = ('P', 'b')  #Row 1 is black's pawns
            board[6][col] = ('P', 'w')  #Row 6 is white's pawns
        return board

    def in_bounds(self, row, col):
        #Checks if a square is inside the 8x8 board
        return 0 <= row < 8 and 0 <= col < 8

    def raw_moves(self, board, row, col, last_move, check_castling=True):
        #Generates all possible moves for a piece, without checking if they leave the king in check
        #last_move is needed for en passant detection
        #check_castling is False when we're checking for attacks (to avoid infinite recursion)
        cell = board[row][col]
        if cell is None:
            return []
        piece, color = cell
        opponent = 'b' if color == 'w' else 'w'
        moves = []

        def slide(delta_row, delta_col):
            #Helper for sliding pieces (bishop, rook, queen) — keeps moving in one direction
            #until hitting the edge of the board or another piece
            new_row = row + delta_row
            new_col = col + delta_col
            while self.in_bounds(new_row, new_col):
                if board[new_row][new_col] is None:
                    moves.append((new_row, new_col))  #Empty square, can keep going
                elif board[new_row][new_col][1] == opponent:
                    moves.append((new_row, new_col))  #Can capture, but must stop
                    break
                else:
                    break  #Blocked by own piece
                new_row += delta_row
                new_col += delta_col

        if piece == 'P':
            forward = -1 if color == 'w' else 1  #White moves up (row decreases), black moves down
            start_row = 6 if color == 'w' else 1  #Starting row for double-move check

            # Move forward one square (only if empty)
            if self.in_bounds(row + forward, col) and board[row + forward][col] is None:
                moves.append((row + forward, col))
                # Move forward two squares from starting position (only if both squares empty)
                if row == start_row and board[row + 2 * forward][col] is None:
                    moves.append((row + 2 * forward, col))

            # Diagonal captures and en passant
            for delta_col in (-1, 1):
                new_row = row + forward
                new_col = col + delta_col
                if self.in_bounds(new_row, new_col):
                    # Normal diagonal capture
                    if board[new_row][new_col] and board[new_row][new_col][1] == opponent:
                        moves.append((new_row, new_col))
                    # En passant — capturing a pawn that just moved two squares forward
                    if last_move:
                        last_src, last_dst, last_piece = last_move
                        if last_piece == 'P' and last_dst[1] == new_col and last_dst[0] == row and abs(last_src[0] - last_dst[0]) == 2:
                            moves.append((new_row, new_col))

        elif piece == 'N':
            #Knights move in an L-shape: 2 squares one way and 1 square perpendicular
            knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                             (1, -2), (1, 2), (2, -1), (2, 1)]
            for delta_row, delta_col in knight_offsets:
                new_row = row + delta_row
                new_col = col + delta_col
                if self.in_bounds(new_row, new_col):
                    if board[new_row][new_col] is None or board[new_row][new_col][1] == opponent:
                        moves.append((new_row, new_col))

        elif piece == 'B':
            #Bishops slide diagonally
            for direction in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                slide(*direction)

        elif piece == 'R':
            #Rooks slide horizontally and vertically
            for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                slide(*direction)

        elif piece == 'Q':
            #Queen slides in all 8 directions (combines bishop + rook)
            for direction in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                slide(*direction)

        elif piece == 'K':
            #King moves one square in any direction
            for delta_row in (-1, 0, 1):
                for delta_col in (-1, 0, 1):
                    if delta_row == 0 and delta_col == 0:
                        continue
                    new_row = row + delta_row
                    new_col = col + delta_col
                    if self.in_bounds(new_row, new_col):
                        if board[new_row][new_col] is None or board[new_row][new_col][1] == opponent:
                            moves.append((new_row, new_col))

            # Castling — king moves 2 squares toward a rook, and the rook jumps over
            # Only allowed if: king hasn't moved, not in check, squares between are empty and not attacked
            if check_castling and not self.has_king_moved(board, row, col) and not self.is_in_check(board, color):
                # Kingside castling (short castle, toward column 7)
                if (board[row][7] == ('R', color) and board[row][5] is None and board[row][6] is None
                        and not self.is_square_attacked(board, row, 5, opponent)
                        and not self.is_square_attacked(board, row, 6, opponent)):
                    moves.append((row, 6))
                # Queenside castling (long castle, toward column 0)
                if (board[row][0] == ('R', color) and board[row][1] is None and board[row][2] is None
                        and board[row][3] is None
                        and not self.is_square_attacked(board, row, 3, opponent)
                        and not self.is_square_attacked(board, row, 2, opponent)):
                    moves.append((row, 2))

        return moves

    def has_king_moved(self, board, row, col):
        #Checks if the king is still on its starting square (used for castling)
        #If the king is not on e1 (white) or e8 (black), it must have moved at some point
        cell = board[row][col]
        if cell is None:
            return True
        piece, color = cell
        king_start = (7, 4) if color == 'w' else (0, 4)
        return piece == 'K' and (row, col) != king_start

    def is_square_attacked(self, board, row, col, by_color):
        #Checks if any piece of by_color can attack the given square
        #Used for check detection and castling validation
        for check_row in range(8):
            for check_col in range(8):
                if board[check_row][check_col] and board[check_row][check_col][1] == by_color:
                    if (row, col) in self.raw_moves(board, check_row, check_col, None, check_castling=False):
                        return True
        return False

    def find_king(self, board, color):
        #Searches the board for the king of the given color and returns its position
        for row in range(8):
            for col in range(8):
                if board[row][col] == ('K', color):
                    return row, col
        return None

    def is_in_check(self, board, color):
        #Returns True if the given color's king is being attacked (in check)
        king_pos = self.find_king(board, color)
        if king_pos is None:
            return False
        opponent = 'b' if color == 'w' else 'w'
        return self.is_square_attacked(board, king_pos[0], king_pos[1], opponent)

    def apply_move(self, board, row, col, new_row, new_col):
        #Creates a new board with the move applied (doesn't modify the original)
        #Also handles special moves: en passant capture, castling rook movement, pawn promotion
        new_board = [row[:] for row in board]
        #Shallow copy is enough because each cell is either None or an immutable tuple
        piece, color = new_board[row][col]
        new_board[new_row][new_col] = new_board[row][col]
        new_board[row][col] = None

        # En passant — pawn moves diagonally but the target square was empty, so capture the pawn beside it
        if piece == 'P' and col != new_col and new_board[new_row][new_col] is None:
            new_board[row][new_col] = None

        # Castling — when the king moves 2 squares, also move the rook to the other side of the king
        if piece == 'K':
            if new_col == col + 2:  #Kingside
                new_board[new_row][7] = None
                new_board[new_row][5] = ('R', color)
            if new_col == col - 2:  #Queenside
                new_board[new_row][0] = None
                new_board[new_row][3] = ('R', color)

        # Pawn promotion — when a pawn reaches the last row, it becomes a queen automatically
        if piece == 'P' and (new_row == 0 or new_row == 7):
            new_board[new_row][new_col] = ('Q', color)

        return new_board

    def get_legal_moves(self, board, row, col, last_move):
        #Returns only the moves that don't leave your own king in check
        #This filters raw_moves by simulating each move and checking if the king is safe afterwards
        piece_color = board[row][col][1]
        legal = []
        for new_row, new_col in self.raw_moves(board, row, col, last_move):
            new_board = self.apply_move(board, row, col, new_row, new_col)
            if not self.is_in_check(new_board, piece_color):
                legal.append((new_row, new_col))
        return legal

    def get_all_legal_moves(self, board, color, last_move):
        #Returns every legal move for all pieces of the given color
        #Each move is a tuple of ((from_row, from_col), (to_row, to_col))
        all_moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col] and board[row][col][1] == color:
                    for destination in self.get_legal_moves(board, row, col, last_move):
                        all_moves.append(((row, col), destination))
        return all_moves

    def square_name(self, row, col):
        #Converts board coordinates to chess notation, e.g. (6, 4) -> "e2"
        return FILE_LETTERS[col] + str(8 - row)

    def get_move_notation(self, piece, source, destination, is_castle_king, is_castle_queen, is_promotion):
        #Creates a readable text representation of a move for the move log
        if is_castle_king:
            return 'O-O'
        if is_castle_queen:
            return 'O-O-O'
        display_piece = 'Q' if is_promotion else piece
        return f"{display_piece}{self.square_name(*source)} -> {display_piece}{self.square_name(*destination)}"


# AI opponent using minimax with alpha-beta pruning
class ChessAI:
    #The AI evaluates board positions and picks the best move using the minimax algorithm
    #Alpha-beta pruning speeds things up by skipping branches that can't possibly be better

    def __init__(self, chess_board, depth=AI_DEPTH, color='b'):
        self.chess_board = chess_board
        self.depth = depth  #How many moves ahead the AI looks
        self.color = color  #Which color the AI is playing as

    def evaluate(self, board):
        #Calculates a score for the current board position
        #Positive score = white is winning, negative = black is winning
        #Uses piece values + piece-square tables to judge how good each piece's position is
        score = 0
        for row in range(8):
            for col in range(8):
                cell = board[row][col]
                if not cell:
                    continue
                piece, color = cell
                # Flip the table index for black pieces so the table is read from their perspective
                table_index = row * 8 + col if color == 'w' else (7 - row) * 8 + col
                value = PIECE_VALUES[piece] + PIECE_SQUARE_TABLES[piece][table_index]
                if color == 'w':
                    score += value
                else:
                    score -= value
        return score

    def _move_sort_key(self, board, destination):
        #Scores a move for ordering: captures of high-value pieces are searched first
        #This makes alpha-beta pruning much more effective because the best moves are tried early,
        #causing more branches to be pruned (skipped)
        target = board[destination[0]][destination[1]]
        if target:
            return -PIECE_VALUES[target[0]]  #Negative so high-value captures come first when sorted
        return 0

    def minimax(self, board, depth, alpha, beta, is_maximizing, last_move):
        #Minimax algorithm — recursively explores all possible moves to find the best one
        #is_maximizing=True means it's white's turn (trying to maximize score)
        #is_maximizing=False means it's black's turn (trying to minimize score)
        #alpha and beta are used for pruning: if we find a move that's already too good/bad,
        #we can skip the rest of the branch because the opponent would never allow it
        color = 'w' if is_maximizing else 'b'
        moves = self.chess_board.get_all_legal_moves(board, color, last_move)

        # No moves available — either checkmate or stalemate
        if not moves:
            if not is_maximizing:
                return 10000, None   #Black has no moves, white wins
            else:
                return -10000, None  #White has no moves, black wins

        # Reached search depth — stop recursing and evaluate the position as-is
        if depth == 0:
            return self.evaluate(board), None

        # Sort moves so captures are searched first (makes alpha-beta pruning way more effective)
        moves.sort(key=lambda m: self._move_sort_key(board, m[1]))

        best_move = None

        if is_maximizing:
            #White's turn — try to find the move that leads to the highest score
            best_score = -999999
            for source, destination in moves:
                new_board = self.chess_board.apply_move(board, source[0], source[1], destination[0], destination[1])
                piece = board[source[0]][source[1]][0]
                child_score, _ = self.minimax(new_board, depth - 1, alpha, beta, False, (source, destination, piece))
                if child_score > best_score:
                    best_score = child_score
                    best_move = (source, destination)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break  #Beta cutoff — black already has a better option, skip this branch
        else:
            #Black's turn — try to find the move that leads to the lowest score
            best_score = 999999
            for source, destination in moves:
                new_board = self.chess_board.apply_move(board, source[0], source[1], destination[0], destination[1])
                piece = board[source[0]][source[1]][0]
                child_score, _ = self.minimax(new_board, depth - 1, alpha, beta, True, (source, destination, piece))
                if child_score < best_score:
                    best_score = child_score
                    best_move = (source, destination)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break  #Alpha cutoff — white already has a better option, skip this branch

        return best_score, best_move

    def think(self, board, last_move, result):
        #Entry point for the AI to pick a move. Runs in a separate thread so the game doesn't freeze
        #result[0] is set to the chosen move, result[1] is the evaluation score
        #The evaluation score is saved for training data collection
        #
        #To add variety, we evaluate all top-level moves and randomly pick from the ones
        #that are within a small margin of the best score. This way the AI still plays well
        #but doesn't always pick the exact same move from the same position.
        is_maximizing = (self.color == 'w')
        color = 'w' if is_maximizing else 'b'
        moves = self.chess_board.get_all_legal_moves(board, color, last_move)

        if not moves:
            result[0] = None
            result.append(0)
            return

        # Score every top-level move
        scored_moves = []
        for source, destination in moves:
            new_board = self.chess_board.apply_move(board, source[0], source[1], destination[0], destination[1])
            piece = board[source[0]][source[1]][0]
            child_score, _ = self.minimax(new_board, self.depth - 1, -999999, 999999, not is_maximizing, (source, destination, piece))
            scored_moves.append((child_score, (source, destination)))

        # Find the best score and collect all moves within a small margin of it
        if is_maximizing:
            best_score = max(s for s, _ in scored_moves)
            margin = 30  #Moves within 30 centipawns of the best are considered equally good
            candidates = [(s, m) for s, m in scored_moves if s >= best_score - margin]
        else:
            best_score = min(s for s, _ in scored_moves)
            margin = 30
            candidates = [(s, m) for s, m in scored_moves if s <= best_score + margin]

        # Randomly pick from the top candidates
        score, move = random.choice(candidates)
        result[0] = move
        result.append(score)
