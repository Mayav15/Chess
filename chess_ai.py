# Chess AI — Board logic and minimax AI with alpha-beta pruning

import copy

FILE_LETTERS = 'abcdefgh'

# Piece-square tables for AI evaluation
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
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


# Board logic and move generation
class ChessBoard:
    def __init__(self):
        self.board = self.create_board()

    def create_board(self):
        back_row = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        board = [[None] * 8 for _ in range(8)]
        for col, piece in enumerate(back_row):
            board[0][col] = (piece, 'b')
            board[7][col] = (piece, 'w')
        for col in range(8):
            board[1][col] = ('P', 'b')
            board[6][col] = ('P', 'w')
        return board

    def in_bounds(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8

    def raw_moves(self, board, row, col, last_move, check_castling=True):
        cell = board[row][col]
        if cell is None:
            return []
        piece, color = cell
        opponent = 'b' if color == 'w' else 'w'
        moves = []

        # Sliding pieces (bishop, rook, queen) share this helper
        def slide(delta_row, delta_col):
            new_row = row + delta_row
            new_col = col + delta_col
            while self.in_bounds(new_row, new_col):
                if board[new_row][new_col] is None:
                    moves.append((new_row, new_col))
                elif board[new_row][new_col][1] == opponent:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += delta_row
                new_col += delta_col

        if piece == 'P':
            forward = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1

            # Move forward one square
            if self.in_bounds(row + forward, col) and board[row + forward][col] is None:
                moves.append((row + forward, col))
                # Move forward two squares from starting position
                if row == start_row and board[row + 2 * forward][col] is None:
                    moves.append((row + 2 * forward, col))

            # Diagonal captures and en passant
            for delta_col in (-1, 1):
                new_row = row + forward
                new_col = col + delta_col
                if self.in_bounds(new_row, new_col):
                    # Normal capture
                    if board[new_row][new_col] and board[new_row][new_col][1] == opponent:
                        moves.append((new_row, new_col))
                    # En passant
                    if last_move:
                        last_src, last_dst, last_piece = last_move
                        if last_piece == 'P' and last_dst[1] == new_col and last_dst[0] == row and abs(last_src[0] - last_dst[0]) == 2:
                            moves.append((new_row, new_col))

        elif piece == 'N':
            knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                             (1, -2), (1, 2), (2, -1), (2, 1)]
            for delta_row, delta_col in knight_offsets:
                new_row = row + delta_row
                new_col = col + delta_col
                if self.in_bounds(new_row, new_col):
                    if board[new_row][new_col] is None or board[new_row][new_col][1] == opponent:
                        moves.append((new_row, new_col))

        elif piece == 'B':
            for direction in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                slide(*direction)

        elif piece == 'R':
            for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                slide(*direction)

        elif piece == 'Q':
            for direction in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                slide(*direction)

        elif piece == 'K':
            for delta_row in (-1, 0, 1):
                for delta_col in (-1, 0, 1):
                    if delta_row == 0 and delta_col == 0:
                        continue
                    new_row = row + delta_row
                    new_col = col + delta_col
                    if self.in_bounds(new_row, new_col):
                        if board[new_row][new_col] is None or board[new_row][new_col][1] == opponent:
                            moves.append((new_row, new_col))

            # Castling
            if check_castling and not self.has_king_moved(board, row, col) and not self.is_in_check(board, color):
                # Kingside castling
                if (board[row][7] == ('R', color) and board[row][5] is None and board[row][6] is None
                        and not self.is_square_attacked(board, row, 5, opponent)
                        and not self.is_square_attacked(board, row, 6, opponent)):
                    moves.append((row, 6))
                # Queenside castling
                if (board[row][0] == ('R', color) and board[row][1] is None and board[row][2] is None
                        and board[row][3] is None
                        and not self.is_square_attacked(board, row, 3, opponent)
                        and not self.is_square_attacked(board, row, 2, opponent)):
                    moves.append((row, 2))

        return moves

    def has_king_moved(self, board, row, col):
        cell = board[row][col]
        if cell is None:
            return True
        piece, color = cell
        king_start = (7, 4) if color == 'w' else (0, 4)
        return piece == 'K' and (row, col) != king_start

    def is_square_attacked(self, board, row, col, by_color):
        for check_row in range(8):
            for check_col in range(8):
                if board[check_row][check_col] and board[check_row][check_col][1] == by_color:
                    if (row, col) in self.raw_moves(board, check_row, check_col, None, check_castling=False):
                        return True
        return False

    def find_king(self, board, color):
        for row in range(8):
            for col in range(8):
                if board[row][col] == ('K', color):
                    return row, col
        return None

    def is_in_check(self, board, color):
        king_pos = self.find_king(board, color)
        if king_pos is None:
            return False
        opponent = 'b' if color == 'w' else 'w'
        return self.is_square_attacked(board, king_pos[0], king_pos[1], opponent)

    def apply_move(self, board, row, col, new_row, new_col):
        new_board = copy.deepcopy(board)
        piece, color = new_board[row][col]
        new_board[new_row][new_col] = new_board[row][col]
        new_board[row][col] = None

        # En passant capture
        if piece == 'P' and col != new_col and new_board[new_row][new_col] is None:
            new_board[row][new_col] = None

        # Castling - move the rook
        if piece == 'K':
            if new_col == col + 2:
                new_board[new_row][7] = None
                new_board[new_row][5] = ('R', color)
            if new_col == col - 2:
                new_board[new_row][0] = None
                new_board[new_row][3] = ('R', color)

        # Pawn promotion (auto-queen)
        if piece == 'P' and (new_row == 0 or new_row == 7):
            new_board[new_row][new_col] = ('Q', color)

        return new_board

    def get_legal_moves(self, board, row, col, last_move):
        piece_color = board[row][col][1]
        legal = []
        for new_row, new_col in self.raw_moves(board, row, col, last_move):
            new_board = self.apply_move(board, row, col, new_row, new_col)
            if not self.is_in_check(new_board, piece_color):
                legal.append((new_row, new_col))
        return legal

    def get_all_legal_moves(self, board, color, last_move):
        all_moves = []
        for row in range(8):
            for col in range(8):
                if board[row][col] and board[row][col][1] == color:
                    for destination in self.get_legal_moves(board, row, col, last_move):
                        all_moves.append(((row, col), destination))
        return all_moves

    def square_name(self, row, col):
        return FILE_LETTERS[col] + str(8 - row)

    def get_move_notation(self, piece, source, destination, is_castle_king, is_castle_queen, is_promotion):
        if is_castle_king:
            return 'O-O'
        if is_castle_queen:
            return 'O-O-O'
        display_piece = 'Q' if is_promotion else piece
        return f"{display_piece}{self.square_name(*source)} -> {display_piece}{self.square_name(*destination)}"


# AI opponent using minimax with alpha-beta pruning
class ChessAI:
    def __init__(self, chess_board, depth=AI_DEPTH, color='b'):
        self.chess_board = chess_board
        self.depth = depth
        self.color = color

    def evaluate(self, board):
        score = 0
        for row in range(8):
            for col in range(8):
                cell = board[row][col]
                if not cell:
                    continue
                piece, color = cell
                table_index = row * 8 + col if color == 'w' else (7 - row) * 8 + col
                value = PIECE_VALUES[piece] + PIECE_SQUARE_TABLES[piece][table_index]
                if color == 'w':
                    score += value
                else:
                    score -= value
        return score

    def minimax(self, board, depth, alpha, beta, is_maximizing, last_move):
        color = 'w' if is_maximizing else 'b'
        moves = self.chess_board.get_all_legal_moves(board, color, last_move)

        # No moves available - checkmate or stalemate
        if not moves:
            if not is_maximizing:
                return 10000, None
            else:
                return -10000, None

        # Reached search depth - evaluate position
        if depth == 0:
            return self.evaluate(board), None

        best_move = None

        if is_maximizing:
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
                    break
        else:
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
                    break

        return best_score, best_move

    def think(self, board, last_move, result):
        is_maximizing = (self.color == 'w')
        _, move = self.minimax(board, self.depth, -999999, 999999, is_maximizing, last_move)
        result[0] = move
