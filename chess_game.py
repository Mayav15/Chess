# Chess Game — Main game loop, rendering, and entry point
# This is the file you run to start the game. It handles drawing the board, pieces, sidebar,
# and all the player interactions (clicking, dragging, scrolling)

import pygame
import sys
import threading
from chess_ai import ChessBoard, ChessAI
from chess_menus import ModeMenu, SinglePlayerMenu, TwoPlayerMenu, PauseMenu
from chess_profiles import ProfileMenu, LoginScreen, SignupScreen
from chess_db import ProfileDB
from game_data_collector import GameDataCollector

pygame.init()
display_info = pygame.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h
#Get the monitor's resolution so we can size the window appropriately

# Colours used throughout the game
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
BACKGROUND = (20, 16, 12)
PANEL_BG = (30, 24, 18)
PANEL_LINE = (55, 44, 33)
HIGHLIGHT_COLOR = (205, 210, 65, 170)     #Yellow-green, for last move highlights
SELECTED_COLOR = (100, 180, 50, 200)      #Green, for the currently selected piece
CHECK_COLOR = (220, 60, 60, 180)          #Red, for the king when in check
MOVE_DOT_COLOR = (80, 140, 40, 160)       #Green dots showing where you can move
CPU_MOVE_COLOR = (80, 160, 220, 150)      #Blue, highlighting the CPU's last move
BORDER_COLOR = (90, 65, 40)
GOLD = (212, 175, 55)
DIM_TEXT = (110, 90, 65)
WHITE_TEXT = (230, 220, 205)
BLACK_SCORE_TEXT = (28, 22, 16)            #Dark text on the white side of the score bar
CPU_SCORE_TEXT = (240, 235, 228)           #Light text on the black side of the score bar

FPS = 60
#Frames per second — how fast the game loop runs

FILE_LETTERS = 'abcdefgh'

# Point values for captured pieces (used in the score bar)
PIECE_SCORE = {'P': 1, 'N': 3, 'B': 3, 'R': 4, 'Q': 9, 'K': 0}

# Display order for captured pieces in the sidebar (most valuable first)
CAPTURE_ORDER = ['Q', 'R', 'B', 'N', 'P']

# Unicode chess piece symbols — used to draw pieces on the board instead of images
UNICODE_PIECES = {
    ('K', 'w'): '♔', ('Q', 'w'): '♕', ('R', 'w'): '♖',
    ('B', 'w'): '♗', ('N', 'w'): '♘', ('P', 'w'): '♙',
    ('K', 'b'): '♚', ('Q', 'b'): '♛', ('R', 'b'): '♜',
    ('B', 'b'): '♝', ('N', 'b'): '♞', ('P', 'b'): '♟',
}


class Layout:
    #Recalculates all layout dimensions based on the current window size
    #This is what makes the game responsive — everything scales with the window

    def __init__(self, width, height):
        self.recalculate(width, height)

    def recalculate(self, width, height):
        self.window_width = width
        self.window_height = height

        self.sidebar_width = max(200, width // 4)
        self.padding = max(16, width // 80)
        self.status_bar_height = 48

        # Calculate the largest board that fits in the available space
        board_max = min(height - self.status_bar_height - self.padding * 2,
                        width - self.sidebar_width - self.padding * 3)
        self.board_size = (board_max // 8) * 8  #Round down to multiple of 8 so cells are even
        self.cell_size = self.board_size // 8

        # Position the board on the left side
        self.board_x = self.padding
        self.board_y = self.status_bar_height + (height - self.status_bar_height - self.board_size) // 2

        # Position the sidebar to the right of the board
        self.sidebar_x = self.board_x + self.board_size + self.padding * 2
        self.sidebar_y = self.status_bar_height + self.padding // 2
        self.sidebar_height = height - self.sidebar_y - self.padding


class ChessRenderer:
    #Handles all the drawing: board squares, pieces, highlights, sidebar, status bar, move log
    #Has a "flipped" mode for when the player is playing as Black (board is rotated 180 degrees)

    def __init__(self, layout, player_name, flipped=False):
        self.layout = layout
        self.player_name = player_name
        self.flipped = flipped
        self.rebuild_fonts()

    def rebuild_fonts(self):
        #Recreates all fonts based on the current cell size (called after window resize)
        cell = self.layout.cell_size
        self.piece_font = pygame.font.SysFont("segoeuisymbol,symbola,freesans,dejavusans", cell - 4)
        self.label_font = pygame.font.SysFont("georgia,serif", max(12, cell // 5))
        self.status_font = pygame.font.SysFont("georgia,serif", max(16, cell // 4), bold=True)
        self.header_font = pygame.font.SysFont("georgia,serif", max(13, cell // 4), bold=True)
        self.mono_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", max(12, cell // 5))
        self.big_font = pygame.font.SysFont("georgia,serif", max(16, cell // 4), bold=True)
        self.small_font = pygame.font.SysFont("georgia,serif", max(11, cell // 6))
        self.capture_font = pygame.font.SysFont("segoeuisymbol,symbola,freesans,dejavusans", max(16, cell // 4))

    def board_to_screen(self, row, col):
        #Converts board coordinates (row, col) to pixel positions on screen
        #When flipped (playing as Black), the board is rotated 180 degrees
        lay = self.layout
        if self.flipped:
            row, col = 7 - row, 7 - col
        return lay.board_x + col * lay.cell_size, lay.board_y + row * lay.cell_size

    def screen_to_board(self, screen_x, screen_y):
        #Converts a mouse click position to board coordinates
        #Returns None if the click is outside the board
        lay = self.layout
        col = (screen_x - lay.board_x) // lay.cell_size
        row = (screen_y - lay.board_y) // lay.cell_size
        if 0 <= row < 8 and 0 <= col < 8:
            if self.flipped:
                row, col = 7 - row, 7 - col
            return (row, col)
        return None

    def draw_board(self, surface, selected, highlights, check_square, move_dots, cpu_highlights):
        #Draws the chess board with all its overlays (highlights, selected square, check, legal moves)
        lay = self.layout
        highlight_surface = pygame.Surface((lay.cell_size, lay.cell_size), pygame.SRCALPHA)
        #SRCALPHA lets us draw semi-transparent overlays on top of the board squares

        # Draw the alternating light/dark squares
        for row in range(8):
            for col in range(8):
                screen_x, screen_y = self.board_to_screen(row, col)
                square_color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(surface, square_color, (screen_x, screen_y, lay.cell_size, lay.cell_size))

        # CPU move highlights (blue tint on the squares the CPU just moved from/to)
        for row, col in cpu_highlights:
            screen_x, screen_y = self.board_to_screen(row, col)
            highlight_surface.fill(CPU_MOVE_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # Last move highlights (yellow tint on source and destination squares)
        for row, col in highlights:
            screen_x, screen_y = self.board_to_screen(row, col)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # Selected square (green tint on the piece you clicked)
        if selected:
            screen_x, screen_y = self.board_to_screen(*selected)
            highlight_surface.fill(SELECTED_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # King in check (red tint on the king's square)
        if check_square:
            screen_x, screen_y = self.board_to_screen(*check_square)
            highlight_surface.fill(CHECK_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # Legal move dots (small green circles on squares you can move to)
        for row, col in move_dots:
            screen_x, screen_y = self.board_to_screen(row, col)
            dot_surface = pygame.Surface((lay.cell_size, lay.cell_size), pygame.SRCALPHA)
            dot_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(dot_surface, MOVE_DOT_COLOR, (lay.cell_size // 2, lay.cell_size // 2), lay.cell_size // 6)
            surface.blit(dot_surface, (screen_x, screen_y))

    def draw_labels(self, surface):
        #Draws the file letters (a-h) along the bottom and rank numbers (1-8) along the left
        #These flip when the board is flipped so the notation stays correct
        lay = self.layout
        label_color = (160, 120, 75)
        for i in range(8):
            # File letters along the bottom
            file_index = 7 - i if self.flipped else i
            file_label = self.label_font.render(FILE_LETTERS[file_index], True, label_color)
            surface.blit(file_label, (lay.board_x + i * lay.cell_size + lay.cell_size // 2 - 6, lay.board_y + lay.board_size + 4))
            # Rank numbers along the left
            rank_number = i + 1 if self.flipped else 8 - i
            rank_label = self.label_font.render(str(rank_number), True, label_color)
            surface.blit(rank_label, (lay.board_x - 18, lay.board_y + i * lay.cell_size + lay.cell_size // 2 - 9))

    def draw_pieces(self, surface, board, dragging=None, drag_pos=None):
        #Draws all pieces on the board using Unicode chess symbols
        #If a piece is being dragged, it's drawn at the cursor position instead of its square
        lay = self.layout
        for row in range(8):
            for col in range(8):
                if dragging and (row, col) == dragging:
                    continue  #Skip the piece being dragged (drawn separately below)
                cell = board[row][col]
                if cell:
                    piece, color = cell
                    character = UNICODE_PIECES[(piece, color)]
                    screen_x, screen_y = self.board_to_screen(row, col)
                    # Shadow behind the piece for better readability
                    surface.blit(self.piece_font.render(character, True, (0, 0, 0)), (screen_x + 3, screen_y + 3))
                    # The actual piece
                    piece_color = (255, 255, 255) if color == 'w' else (22, 14, 8)
                    surface.blit(self.piece_font.render(character, True, piece_color), (screen_x + 2, screen_y))

        # Draw the piece being dragged at the cursor position
        if dragging and drag_pos:
            cell = board[dragging[0]][dragging[1]]
            if cell:
                piece, color = cell
                character = UNICODE_PIECES[(piece, color)]
                cursor_x, cursor_y = drag_pos
                piece_color = (255, 255, 255) if color == 'w' else (22, 14, 8)
                surface.blit(self.piece_font.render(character, True, piece_color),
                             (cursor_x - lay.cell_size // 2 + 2, cursor_y - lay.cell_size // 2))

    def draw_status_bar(self, surface, turn, status, is_thinking, white_name, black_name):
        #Draws the status bar at the top showing whose turn it is, or game-over messages
        lay = self.layout
        current_name = white_name if turn == 'w' else black_name
        other_name = black_name if turn == 'w' else white_name
        color_label = "White" if turn == 'w' else "Black"

        if status == 'checkmate':
            message = f"Checkmate! {other_name} wins!"
        elif status == 'stalemate':
            message = "Stalemate — Draw!"
        elif status == 'forfeit':
            message = "Game forfeited"
        elif is_thinking:
            message = "CPU is thinking…"
        elif status == 'check':
            message = f"Check!  —  {current_name}'s move"
        else:
            message = f"{current_name}'s move  ({color_label})"

        text = self.status_font.render(message, True, WHITE_TEXT)
        text_x = (lay.board_x + lay.board_size // 2) - text.get_width() // 2
        text_y = (lay.status_bar_height - text.get_height()) // 2
        surface.blit(text, (text_x, text_y))

    def draw_sidebar(self, surface, white_score, black_score, white_captures, black_captures, move_log, scroll, white_name="Player", black_name="CPU"):
        #Draws the entire sidebar panel: score bar, captured pieces, and move log
        lay = self.layout
        sidebar_x = lay.sidebar_x
        sidebar_y = lay.sidebar_y
        sidebar_w = lay.sidebar_width
        sidebar_h = lay.sidebar_height

        # Panel background with rounded corners
        pygame.draw.rect(surface, PANEL_BG, (sidebar_x, sidebar_y, sidebar_w, sidebar_h), border_radius=10)
        pygame.draw.rect(surface, PANEL_LINE, (sidebar_x, sidebar_y, sidebar_w, sidebar_h), 1, border_radius=10)

        current_y = sidebar_y + 14

        # --- SCORE SECTION ---
        score_header = self.header_font.render("SCORE", True, GOLD)
        surface.blit(score_header, (sidebar_x + sidebar_w // 2 - score_header.get_width() // 2, current_y))
        current_y += score_header.get_height() + 8

        # Score bar — a horizontal bar split proportionally between white and black scores
        bar_x = sidebar_x + 14
        bar_width = sidebar_w - 28
        bar_height = 32
        total_score = max(1, white_score + black_score)  #Avoid division by zero
        white_fraction = white_score / total_score

        # Background track
        pygame.draw.rect(surface, (40, 32, 24), (bar_x, current_y, bar_width, bar_height), border_radius=8)

        # White portion (left side of the bar)
        if white_score > 0:
            white_bar_width = max(1, int(bar_width * white_fraction))
            radius = 8 if black_score == 0 else 0  #Round corners only if it fills the whole bar
            pygame.draw.rect(surface, (225, 215, 195), (bar_x, current_y, white_bar_width, bar_height), border_radius=radius)
            pygame.draw.rect(surface, (225, 215, 195), (bar_x, current_y, min(8, white_bar_width), bar_height))
            pygame.draw.rect(surface, (225, 215, 195), (bar_x, current_y, white_bar_width, bar_height), border_radius=radius)

        # Black portion (right side of the bar)
        if black_score > 0:
            black_bar_width = bar_width - int(bar_width * white_fraction)
            black_bar_x = bar_x + int(bar_width * white_fraction)
            radius = 8 if white_score == 0 else 0
            pygame.draw.rect(surface, (55, 44, 33), (black_bar_x, current_y, black_bar_width, bar_height), border_radius=radius)

        # Bar outline
        pygame.draw.rect(surface, PANEL_LINE, (bar_x, current_y, bar_width, bar_height), 1, border_radius=8)

        # Score numbers on each end of the bar
        white_score_text = self.big_font.render(str(white_score), True, BLACK_SCORE_TEXT)
        black_score_text = self.big_font.render(str(black_score), True, CPU_SCORE_TEXT)
        surface.blit(white_score_text, (bar_x + 6, current_y + bar_height // 2 - white_score_text.get_height() // 2))
        surface.blit(black_score_text, (bar_x + bar_width - black_score_text.get_width() - 6, current_y + bar_height // 2 - black_score_text.get_height() // 2))
        current_y += bar_height + 4

        # Player name labels under the score bar
        left_label = self.small_font.render(f"{white_name} (White)", True, (170, 160, 145))
        right_label = self.small_font.render(f"{black_name} (Black)", True, (100, 88, 70))
        surface.blit(left_label, (bar_x, current_y))
        surface.blit(right_label, (bar_x + bar_width - right_label.get_width(), current_y))
        current_y += left_label.get_height() + 12

        # --- CAPTURES SECTION ---
        pygame.draw.line(surface, PANEL_LINE, (sidebar_x + 10, current_y), (sidebar_x + sidebar_w - 10, current_y))
        current_y += 8

        captures_header = self.header_font.render("CAPTURES", True, GOLD)
        surface.blit(captures_header, (sidebar_x + sidebar_w // 2 - captures_header.get_width() // 2, current_y))
        current_y += captures_header.get_height() + 6

        # Show which pieces each player has captured
        current_y = self.draw_capture_row(surface, white_captures, 'b', f"{white_name} captured:", current_y, sidebar_x, sidebar_w)
        current_y = self.draw_capture_row(surface, black_captures, 'w', f"{black_name} captured:", current_y, sidebar_x, sidebar_w)
        current_y += 4

        # --- MOVE LOG SECTION ---
        pygame.draw.line(surface, PANEL_LINE, (sidebar_x + 10, current_y), (sidebar_x + sidebar_w - 10, current_y))
        current_y += 8

        move_log_header = self.header_font.render("MOVE LOG", True, GOLD)
        surface.blit(move_log_header, (sidebar_x + sidebar_w // 2 - move_log_header.get_width() // 2, current_y))
        current_y += move_log_header.get_height() + 6

        scroll = self.draw_move_log(surface, move_log, scroll, current_y, sidebar_x, sidebar_y, sidebar_w, sidebar_h, white_name, black_name)
        return scroll

    def draw_capture_row(self, surface, pieces, show_as_color, label_text, current_y, sidebar_x, sidebar_w):
        #Draws a row of captured pieces (e.g. "Player captured: ♛♜♟♟")
        #Pieces are sorted by value (most valuable first) and wrap to the next line if needed
        sorted_pieces = sorted(pieces, key=lambda p: CAPTURE_ORDER.index(p) if p in CAPTURE_ORDER else 99)

        label = self.small_font.render(label_text, True, DIM_TEXT)
        surface.blit(label, (sidebar_x + 10, current_y))
        current_y += label.get_height() + 2

        draw_x = sidebar_x + 10
        for piece in sorted_pieces:
            character = UNICODE_PIECES[(piece, show_as_color)]
            piece_color = (240, 230, 215) if show_as_color == 'w' else (38, 28, 18)
            piece_image = self.capture_font.render(character, True, piece_color)
            if draw_x + piece_image.get_width() > sidebar_x + sidebar_w - 10:
                draw_x = sidebar_x + 10  #Wrap to next line
                current_y += piece_image.get_height() + 1
            surface.blit(piece_image, (draw_x, current_y))
            draw_x += piece_image.get_width() + 2

        return current_y + self.capture_font.get_height() + 6

    def draw_move_log(self, surface, move_log, scroll, log_top, sidebar_x, sidebar_y, sidebar_w, sidebar_h, white_name="Player", black_name="CPU"):
        #Draws the scrollable move log showing all moves played so far
        #Each entry shows: move number, player name tag, and the move notation
        log_height = sidebar_y + sidebar_h - log_top - 10
        log_rect = pygame.Rect(sidebar_x + 6, log_top, sidebar_w - 12, log_height)

        row_height = self.mono_font.get_height() + 4
        total_rows = len(move_log)
        visible_rows = max(1, log_height // row_height)
        max_scroll = max(0, total_rows - visible_rows)
        scroll = max(0, min(scroll, max_scroll))  #Clamp scroll within bounds

        # Clip drawing to the log area so text doesn't overflow
        old_clip = surface.get_clip()
        surface.set_clip(log_rect)

        for i in range(total_rows):
            row_y = log_top + (i - scroll) * row_height
            if row_y + row_height < log_top or row_y > log_top + log_height:
                continue  #Skip rows that are scrolled out of view

            entry = move_log[i]
            is_last_entry = (i == total_rows - 1)
            is_white_move = entry['color'] == 'w'

            # Alternating row shading for readability
            if i % 2 == 0:
                pygame.draw.rect(surface, (36, 28, 20), (sidebar_x + 6, row_y, sidebar_w - 12, row_height))

            # Move number
            number_text = self.mono_font.render(f"{entry['num']}.", True, DIM_TEXT)
            surface.blit(number_text, (sidebar_x + 10, row_y + 1))

            # Player name tag (e.g. [Player] or [CPU])
            tag = white_name if is_white_move else black_name
            tag_color = (200, 190, 170) if is_white_move else (120, 150, 200)
            player_text = self.mono_font.render(f"[{tag}]", True, tag_color)
            surface.blit(player_text, (sidebar_x + 10 + number_text.get_width() + 4, row_y + 1))

            # The move itself (e.g. "Pe2 -> Pe4") — the latest move is highlighted
            if is_last_entry and is_white_move:
                move_color = GOLD
            elif is_last_entry and not is_white_move:
                move_color = (140, 200, 255)
            else:
                move_color = WHITE_TEXT
            move_text = self.mono_font.render(entry['text'], True, move_color)
            surface.blit(move_text, (sidebar_x + 10 + number_text.get_width() + player_text.get_width() + 8, row_y + 1))

        surface.set_clip(old_clip)  #Restore the original clip area

        # Show scroll hint if the log is too long to fit
        if total_rows > visible_rows:
            hint = self.small_font.render("scroll ↑↓", True, (75, 60, 45))
            surface.blit(hint, (sidebar_x + sidebar_w - hint.get_width() - 8, sidebar_y + sidebar_h - hint.get_height() - 4))

        return scroll


class ChessGame:
    #Main game class — manages all the game state (board, turns, scores, move history)
    #and ties together the AI, renderer, and event handling

    def __init__(self, screen, clock, layout, player_name, difficulty=2, player_color='w',
                 two_player=False, player2_name="Player 2", logged_in_user=None, db=None):
        self.screen = screen
        self.clock = clock
        self.layout = layout
        self.player_name = player_name
        self.player2_name = player2_name
        self.difficulty = difficulty
        self.two_player = two_player
        self.logged_in_user = logged_in_user  #None for guest, otherwise dict from ProfileDB
        self.db = db  #Database connection (used to update stats when game ends)
        self.stats_recorded = False  #Prevent recording twice if save is called multiple times
        self.human_color = player_color
        self.cpu_color = 'b' if player_color == 'w' else 'w'
        self.flipped = (player_color == 'b') if not two_player else False
        #When playing as Black, flip the board so Black is at the bottom

        self.chess_board = ChessBoard()
        if not two_player:
            self.ai = ChessAI(self.chess_board, depth=difficulty, color=self.cpu_color)
        else:
            self.ai = None  #No AI needed in 2 player mode
        self.renderer = ChessRenderer(self.layout, self.player_name, self.flipped)
        self.pause_menu = PauseMenu(self.screen, self.clock)

        # Data collector — silently records every game for future neural network training
        self.collector = GameDataCollector(
            mode='cpu' if not two_player else '2player',
            difficulty=difficulty if not two_player else None
        )
        self.cpu_eval_score = None  #Stores the CPU's minimax evaluation for data collection

        self.move_counter = 0
        self.reset_game()

    def handle_resize(self, new_width, new_height):
        #Called when the window is resized — recalculates layout and rebuilds fonts
        new_width = max(640, new_width)   #Minimum window size
        new_height = max(480, new_height)
        self.layout.recalculate(new_width, new_height)
        self.renderer.rebuild_fonts()
        self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

    def reset_game(self):
        #Sets everything back to the starting position
        self.move_counter = 0
        self.board = self.chess_board.create_board()
        self.turn = 'w'  #White always goes first
        self.selected = None
        self.highlights = []
        self.cpu_highlights = []
        self.move_dots = []
        self.last_move = None
        self.status = 'normal'
        self.dragging = None
        self.drag_pos = None
        self.check_square = None
        self.cpu_thinking = False
        self.cpu_result = [None]  #List so the thread can write to it
        self.cpu_thread = None
        self.white_score = 0
        self.black_score = 0
        self.white_captures = []
        self.black_captures = []
        self.move_log = []
        self.scroll = 0
        self.move_history = {}  #Tracks how many times each move has been made by each side
        self.update_status()

        # If human plays Black in single-player, the CPU (White) moves first
        if not self.two_player and self.human_color == 'b':
            self.start_cpu_turn()

    def update_status(self):
        #Checks if the current player is in check, checkmate, or stalemate
        moves = self.chess_board.get_all_legal_moves(self.board, self.turn, self.last_move)
        if not moves:
            if self.chess_board.is_in_check(self.board, self.turn):
                self.status = 'checkmate'  #No legal moves + in check = checkmate
                self.check_square = self.chess_board.find_king(self.board, self.turn)
            else:
                self.status = 'stalemate'  #No legal moves + not in check = stalemate (draw)
                self.check_square = None
        elif self.chess_board.is_in_check(self.board, self.turn):
            self.status = 'check'
            self.check_square = self.chess_board.find_king(self.board, self.turn)
        else:
            self.status = 'normal'
            self.check_square = None

    def commit_move(self, source, destination):
        #Applies a move to the board, updates scores, captures, and the move log
        board_before = [row[:] for row in self.board]  #Snapshot for data collection
        piece = self.board[source[0]][source[1]][0]
        mover_color = self.board[source[0]][source[1]][1]
        captured_cell = self.board[destination[0]][destination[1]]

        # Check for en passant capture (pawn moves diagonally to an empty square)
        en_passant_capture = None
        if piece == 'P' and source[1] != destination[1] and captured_cell is None:
            en_passant_capture = self.board[source[0]][destination[1]]
        actual_capture = captured_cell or en_passant_capture

        is_castle_kingside = piece == 'K' and destination[1] - source[1] == 2
        is_castle_queenside = piece == 'K' and source[1] - destination[1] == 2
        is_promotion = piece == 'P' and (destination[0] == 0 or destination[0] == 7)

        # Apply the move to the board
        self.last_move = (source, destination, piece)
        self.board = self.chess_board.apply_move(self.board, source[0], source[1], destination[0], destination[1])
        self.turn = 'b' if self.turn == 'w' else 'w'  #Switch turns
        self.selected = None
        self.move_dots = []
        self.highlights = [source, destination]  #Highlight the move that was just made
        self.update_status()

        # Track move repetition — if the same move is made 10 times by one side, it's a draw
        move_key = (mover_color, source, destination)
        self.move_history[move_key] = self.move_history.get(move_key, 0) + 1
        if self.move_history[move_key] >= 10 and self.status not in ('checkmate', 'stalemate'):
            self.status = 'stalemate'
            self.check_square = None

        # Only kings left on the board — no one can win, it's a draw
        if self.status not in ('checkmate', 'stalemate'):
            pieces_left = [cell for row in self.board for cell in row if cell is not None]
            if all(piece == 'K' for piece, _ in pieces_left):
                self.status = 'stalemate'
                self.check_square = None

        # Update captures and score if a piece was taken
        if actual_capture:
            captured_piece = actual_capture[0]
            points = PIECE_SCORE.get(captured_piece, 0)
            if mover_color == 'w':
                self.white_score += points
                self.white_captures.append(captured_piece)
            else:
                self.black_score += points
                self.black_captures.append(captured_piece)

        # Add the move to the move log
        self.move_counter += 1
        notation = self.chess_board.get_move_notation(piece, source, destination, is_castle_kingside, is_castle_queenside, is_promotion)
        self.move_log.append({'num': self.move_counter, 'color': mover_color, 'text': notation})

        # Auto-scroll to the bottom of the move log
        self.scroll = len(self.move_log)

        # Record this move for training data collection
        # CPU moves in 1P games include the minimax evaluation score
        evaluation = None
        if not self.two_player and mover_color == self.cpu_color:
            evaluation = self.cpu_eval_score
        self.collector.record_move(board_before, mover_color, source, destination, notation, evaluation)

    def start_cpu_turn(self):
        #Starts the AI thinking in a background thread so the game doesn't freeze while it calculates
        self.cpu_thinking = True
        self.cpu_result = [None]
        thread = threading.Thread(target=self.ai.think, args=(self.board, self.last_move, self.cpu_result), daemon=True)
        #daemon=True means the thread will be killed when the main program exits
        thread.start()
        self.cpu_thread = thread

    def _save_game_data(self):
        #Determines the game outcome and saves the recorded data to a JSON file
        if self.status == 'checkmate':
            winner = 'b' if self.turn == 'w' else 'w'  #The player whose turn it is got checkmated
            result = 'white_win' if winner == 'w' else 'black_win'
        elif self.status == 'stalemate':
            result = 'draw'
        else:
            result = 'forfeit'
        self.collector.set_result(result)
        self.collector.save()
        #Update the logged-in player's profile stats (skipped for guests and 2P games)
        self._record_stats(result)

    def _record_stats(self, result):
        #Updates the logged-in user's win/loss/draw count in the database
        #Only runs if a profile is logged in. 2P games don't update stats since two
        #people share one keyboard — we don't know which one is the logged-in player
        if self.stats_recorded or not self.logged_in_user or not self.db or self.two_player:
            return

        #Figure out the result from the logged-in player's perspective
        if result == 'draw':
            stat_result = 'draw'
        elif result == 'forfeit':
            stat_result = 'loss'  #1P forfeit always counts as a loss for the human
        elif result == 'white_win':
            stat_result = 'win' if self.human_color == 'w' else 'loss'
        elif result == 'black_win':
            stat_result = 'win' if self.human_color == 'b' else 'loss'
        else:
            return

        self.db.update_stats(self.logged_in_user['id'], stat_result)
        self.stats_recorded = True

    def select_piece(self, row, col):
        #Selects a piece at the given square (if it belongs to the current player)
        #and shows the legal moves as green dots
        allowed_color = self.turn if self.two_player else self.human_color
        if self.board[row][col] and self.board[row][col][1] == allowed_color:
            self.selected = (row, col)
            self.move_dots = self.chess_board.get_legal_moves(self.board, row, col, self.last_move)
        else:
            self.selected = None
            self.move_dots = []

    def try_human_move(self, row, col):
        #Tries to move the selected piece to the clicked square
        #If the move is legal, commits it. If not, tries to select a new piece instead
        if self.selected is None:
            return
        selected_row, selected_col = self.selected
        legal = self.chess_board.get_legal_moves(self.board, selected_row, selected_col, self.last_move)
        if (row, col) in legal:
            self.commit_move(self.selected, (row, col))
            self.cpu_highlights = []
            # In 1P mode, start the CPU's turn after the human moves
            if not self.two_player and self.turn == self.cpu_color and self.status not in ('checkmate', 'stalemate'):
                self.start_cpu_turn()
        else:
            self.select_piece(row, col)  #Clicked an invalid square, try selecting instead

    def show_pause_menu(self):
        #Opens the pause menu overlay. Returns 'main_menu' if the player forfeits/quits, else 'resume'
        self.draw()  #Draw the game one more time so it shows behind the overlay
        if self.two_player:
            white_label = f"{self.player_name} (W)"
            black_label = f"{self.player2_name} (B)"
        else:
            if self.human_color == 'w':
                white_label = self.player_name
                black_label = "CPU"
            else:
                white_label = "CPU"
                black_label = self.player_name
        result = self.pause_menu.run(white_label, black_label, self.white_score, self.black_score, self.two_player)
        if result in ('forfeit', 'quit'):
            self.cpu_thinking = False
            self._save_game_data()  #Save game data before returning to menu
            return 'main_menu'
        return 'resume'

    def handle_events(self):
        #Processes all pygame events (keyboard, mouse, window resize, etc.)
        #Returns 'quit' to close the game, 'main_menu' to go back, or 'continue' to keep playing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            elif event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.status in ('checkmate', 'stalemate'):
                        #Game is over — save data and go back to the main menu
                        self._save_game_data()
                        return 'main_menu'
                    else:
                        result = self.show_pause_menu()
                        if result == 'main_menu':
                            return 'main_menu'
                elif event.key == pygame.K_UP:
                    self.scroll = max(0, self.scroll - 1)  #Scroll move log up
                elif event.key == pygame.K_DOWN:
                    self.scroll += 1  #Scroll move log down

            elif event.type == pygame.MOUSEWHEEL:
                self.scroll = max(0, self.scroll - event.y)  #Mouse wheel scrolls the move log

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left click — select a piece or make a move
                can_interact = self.status not in ('checkmate', 'stalemate')
                if not self.two_player:
                    can_interact = can_interact and self.turn == self.human_color and not self.cpu_thinking
                if can_interact:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    square = self.renderer.screen_to_board(mouse_x, mouse_y)
                    allowed_color = self.turn if self.two_player else self.human_color
                    if square:
                        row, col = square
                        if self.selected:
                            # Already have a piece selected — try to move it there
                            selected_row, selected_col = self.selected
                            legal = self.chess_board.get_legal_moves(self.board, selected_row, selected_col, self.last_move)
                            if (row, col) in legal:
                                self.try_human_move(row, col)
                            else:
                                # Clicked somewhere else — try selecting a new piece
                                self.select_piece(row, col)
                                if self.board[row][col] and self.board[row][col][1] == allowed_color:
                                    self.dragging = (row, col)  #Start dragging
                        else:
                            # No piece selected — try to select one
                            self.select_piece(row, col)
                            if self.board[row][col] and self.board[row][col][1] == allowed_color:
                                self.dragging = (row, col)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Mouse released — if we were dragging a piece, try to drop it
                if self.dragging:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    square = self.renderer.screen_to_board(mouse_x, mouse_y)
                    if square and self.status not in ('checkmate', 'stalemate'):
                        self.try_human_move(square[0], square[1])
                    self.dragging = None
                    self.drag_pos = None

        return 'continue'

    def draw(self):
        #Renders the entire game screen: background, board, pieces, status bar, sidebar
        lay = self.layout
        self.screen.fill(BACKGROUND)

        # Status bar background (dark bar across the top)
        pygame.draw.rect(self.screen, (28, 22, 16), (0, 0, lay.window_width, lay.status_bar_height))
        pygame.draw.line(self.screen, PANEL_LINE, (0, lay.status_bar_height), (lay.window_width, lay.status_bar_height))

        # Board border
        pygame.draw.rect(self.screen, BORDER_COLOR,
                         (lay.board_x - 5, lay.board_y - 5, lay.board_size + 10, lay.board_size + 10), 5, border_radius=4)

        # Board, labels, and pieces
        self.renderer.draw_board(self.screen, self.selected, self.highlights,
                                 self.check_square, self.move_dots, self.cpu_highlights)
        self.renderer.draw_labels(self.screen)
        self.renderer.draw_pieces(self.screen, self.board, dragging=self.dragging, drag_pos=self.drag_pos)

        # Figure out who is White and who is Black for labels
        if self.two_player:
            white_name, black_name = self.player_name, self.player2_name
        elif self.human_color == 'w':
            white_name, black_name = self.player_name, "CPU"
        else:
            white_name, black_name = "CPU", self.player_name
        self.renderer.draw_status_bar(self.screen, self.turn, self.status, self.cpu_thinking, white_name, black_name)

        # Animated thinking dots while CPU is calculating ("CPU is thinking...")
        if self.cpu_thinking:
            num_dots = pygame.time.get_ticks() // 400 % 4  #Cycles through 0, 1, 2, 3 dots
            dots = '.' * num_dots
            dots_text = self.renderer.status_font.render(dots, True, (160, 140, 100))
            self.screen.blit(dots_text, (lay.board_x + lay.board_size // 2 + 140, (lay.status_bar_height - self.renderer.status_font.get_height()) // 2))

        # Keyboard hint at the bottom
        hint = self.renderer.label_font.render("ESC=menu", True, (70, 55, 40))
        self.screen.blit(hint, (lay.board_x, lay.window_height - hint.get_height() - 6))

        # Sidebar (score, captures, move log)
        self.scroll = self.renderer.draw_sidebar(self.screen, self.white_score, self.black_score,
                                                  self.white_captures, self.black_captures,
                                                  self.move_log, self.scroll, white_name, black_name)

        pygame.display.flip()
        #.flip() updates the entire screen at once, so all changes appear together

    def run(self):
        #Main game loop — runs every frame until the game ends or the player quits
        while True:
            self.clock.tick(FPS)
            #.tick(FPS) caps the frame rate so the game runs at the same speed on all computers

            # Update drag position to follow the mouse
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.dragging:
                self.drag_pos = (mouse_x, mouse_y)

            # Check if the CPU finished thinking (the AI thread writes to cpu_result)
            if self.cpu_thinking and self.cpu_result[0] is not None:
                self.cpu_thinking = False
                source, destination = self.cpu_result[0]
                # Grab the evaluation score for data collection (appended by think())
                self.cpu_eval_score = self.cpu_result[1] if len(self.cpu_result) > 1 else None
                self.commit_move(source, destination)
                self.cpu_highlights = [source, destination]  #Show where the CPU moved

            # Handle input events
            result = self.handle_events()
            if result == 'quit':
                return 'quit'
            if result == 'main_menu':
                return 'main_menu'

            # Render everything
            self.draw()


def _handle_profile_flow(screen, clock, db, logged_in_user):
    #Shows the profile menu and handles login/signup/guest/logout actions
    #Returns the (possibly updated) logged_in_user
    profile_menu = ProfileMenu(screen, clock, db, logged_in_user)
    result = profile_menu.run()
    action = result['action']

    if action == 'login':
        login_screen = LoginScreen(screen, clock, db)
        user = login_screen.run()
        if user:
            return user
    elif action == 'signup':
        signup_screen = SignupScreen(screen, clock, db)
        user = signup_screen.run()
        if user:
            return user
    elif action == 'guest':
        return None  #Play as guest = no logged-in user
    elif action == 'logout':
        return None  #Logging out also clears the user
    #'back' or any other case: keep the current logged_in_user as-is
    return logged_in_user


def main():
    #Entry point — sets up the window and runs the menu → game loop
    layout = Layout(int(SCREEN_WIDTH * 0.9), int(SCREEN_HEIGHT * 0.9))
    #Start the window at 90% of the screen size

    screen = pygame.display.set_mode((layout.window_width, layout.window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()

    # Open the database once at startup; all menus and games share this connection
    db = ProfileDB()
    logged_in_user = None  #None means "playing as guest"

    while True:
        # Step 1: Choose game mode (or open Profiles)
        mode_menu = ModeMenu(screen, clock, logged_in_user=logged_in_user)
        mode = mode_menu.run()

        # Profiles button — show the profile screen and loop back to the mode menu
        if mode == 'profiles':
            screen = pygame.display.get_surface()
            logged_in_user = _handle_profile_flow(screen, clock, db, logged_in_user)
            #After login/signup, fetch the latest user data so stats panel is up to date
            if logged_in_user:
                logged_in_user = db.get_user(logged_in_user['id'])
            continue

        # Step 2: Show the settings screen for the chosen mode
        #Pre-fill the player name from the logged-in profile if there is one
        default_name = logged_in_user['username'] if logged_in_user else ""
        screen = pygame.display.get_surface()
        if mode == '1player':
            menu = SinglePlayerMenu(screen, clock, default_name=default_name)
        else:
            menu = TwoPlayerMenu(screen, clock, default_name=default_name)
        settings = menu.run()

        # If they pressed ESC or Back, go back to mode selection
        if settings is None:
            screen = pygame.display.get_surface()
            continue

        # Update screen reference in case it was resized during the menus
        screen = pygame.display.get_surface()
        width, height = screen.get_size()
        layout.recalculate(width, height)

        # Step 3: Start the game with the chosen settings
        if settings['mode'] == 'cpu':
            game = ChessGame(screen, clock, layout, settings['player_name'],
                             difficulty=settings['difficulty'], player_color=settings['player_color'],
                             logged_in_user=logged_in_user, db=db)
        else:
            game = ChessGame(screen, clock, layout, settings['player_name'],
                             two_player=True, player2_name=settings['player2_name'],
                             logged_in_user=logged_in_user, db=db)
        result = game.run()

        # Refresh the logged-in user's data so the stats panel reflects the new game
        if logged_in_user:
            logged_in_user = db.get_user(logged_in_user['id'])

        if result == 'quit':
            break
        # result == 'main_menu' loops back to the mode selection screen

    db.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
