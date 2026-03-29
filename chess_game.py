# Chess vs CPU — Single player chess game using Pygame
# Play as White or Black against a CPU opponent (minimax AI with alpha-beta pruning)

import pygame
import sys
import threading
from chess_ai import ChessBoard, ChessAI
from chess_menus import StartMenu, PauseMenu

pygame.init()
display_info = pygame.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h

# Colours
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
BACKGROUND = (20, 16, 12)
PANEL_BG = (30, 24, 18)
PANEL_LINE = (55, 44, 33)
HIGHLIGHT_COLOR = (205, 210, 65, 170)
SELECTED_COLOR = (100, 180, 50, 200)
CHECK_COLOR = (220, 60, 60, 180)
MOVE_DOT_COLOR = (80, 140, 40, 160)
CPU_MOVE_COLOR = (80, 160, 220, 150)
BORDER_COLOR = (90, 65, 40)
GOLD = (212, 175, 55)
DIM_TEXT = (110, 90, 65)
WHITE_TEXT = (230, 220, 205)
BLACK_SCORE_TEXT = (28, 22, 16)
CPU_SCORE_TEXT = (240, 235, 228)

FPS = 60

FILE_LETTERS = 'abcdefgh'

# Point values for captured pieces
PIECE_SCORE = {'P': 1, 'N': 3, 'B': 3, 'R': 4, 'Q': 9, 'K': 0}

# Display order for captures (descending value)
CAPTURE_ORDER = ['Q', 'R', 'B', 'N', 'P']

# Unicode chess piece symbols
UNICODE_PIECES = {
    ('K', 'w'): '♔', ('Q', 'w'): '♕', ('R', 'w'): '♖',
    ('B', 'w'): '♗', ('N', 'w'): '♘', ('P', 'w'): '♙',
    ('K', 'b'): '♚', ('Q', 'b'): '♛', ('R', 'b'): '♜',
    ('B', 'b'): '♝', ('N', 'b'): '♞', ('P', 'b'): '♟',
}


# Recalculates all layout dimensions based on current window size
class Layout:
    def __init__(self, width, height):
        self.recalculate(width, height)

    def recalculate(self, width, height):
        self.window_width = width
        self.window_height = height

        self.sidebar_width = max(200, width // 4)
        self.padding = max(16, width // 80)
        self.status_bar_height = 48

        board_max = min(height - self.status_bar_height - self.padding * 2,
                        width - self.sidebar_width - self.padding * 3)
        self.board_size = (board_max // 8) * 8
        self.cell_size = self.board_size // 8

        self.board_x = self.padding
        self.board_y = self.status_bar_height + (height - self.status_bar_height - self.board_size) // 2

        self.sidebar_x = self.board_x + self.board_size + self.padding * 2
        self.sidebar_y = self.status_bar_height + self.padding // 2
        self.sidebar_height = height - self.sidebar_y - self.padding



# Handles all rendering (board, pieces, sidebar, status bar)
class ChessRenderer:
    def __init__(self, layout, player_name, flipped=False):
        self.layout = layout
        self.player_name = player_name
        self.flipped = flipped
        self.rebuild_fonts()

    def rebuild_fonts(self):
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
        lay = self.layout
        if self.flipped:
            row, col = 7 - row, 7 - col
        return lay.board_x + col * lay.cell_size, lay.board_y + row * lay.cell_size

    def screen_to_board(self, screen_x, screen_y):
        lay = self.layout
        col = (screen_x - lay.board_x) // lay.cell_size
        row = (screen_y - lay.board_y) // lay.cell_size
        if 0 <= row < 8 and 0 <= col < 8:
            if self.flipped:
                row, col = 7 - row, 7 - col
            return (row, col)
        return None

    def draw_board(self, surface, selected, highlights, check_square, move_dots, cpu_highlights):
        lay = self.layout
        highlight_surface = pygame.Surface((lay.cell_size, lay.cell_size), pygame.SRCALPHA)

        # Draw the squares
        for row in range(8):
            for col in range(8):
                screen_x, screen_y = self.board_to_screen(row, col)
                square_color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(surface, square_color, (screen_x, screen_y, lay.cell_size, lay.cell_size))

        # CPU move highlights (blue)
        for row, col in cpu_highlights:
            screen_x, screen_y = self.board_to_screen(row, col)
            highlight_surface.fill(CPU_MOVE_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # Last move highlights (yellow)
        for row, col in highlights:
            screen_x, screen_y = self.board_to_screen(row, col)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # Selected square (green)
        if selected:
            screen_x, screen_y = self.board_to_screen(*selected)
            highlight_surface.fill(SELECTED_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # King in check (red)
        if check_square:
            screen_x, screen_y = self.board_to_screen(*check_square)
            highlight_surface.fill(CHECK_COLOR)
            surface.blit(highlight_surface, (screen_x, screen_y))

        # Legal move dots
        for row, col in move_dots:
            screen_x, screen_y = self.board_to_screen(row, col)
            dot_surface = pygame.Surface((lay.cell_size, lay.cell_size), pygame.SRCALPHA)
            dot_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(dot_surface, MOVE_DOT_COLOR, (lay.cell_size // 2, lay.cell_size // 2), lay.cell_size // 6)
            surface.blit(dot_surface, (screen_x, screen_y))

    def draw_labels(self, surface):
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
        lay = self.layout
        for row in range(8):
            for col in range(8):
                # Skip the piece being dragged
                if dragging and (row, col) == dragging:
                    continue
                cell = board[row][col]
                if cell:
                    piece, color = cell
                    character = UNICODE_PIECES[(piece, color)]
                    screen_x, screen_y = self.board_to_screen(row, col)
                    # Shadow
                    surface.blit(self.piece_font.render(character, True, (0, 0, 0)), (screen_x + 3, screen_y + 3))
                    # Piece
                    piece_color = (255, 255, 255) if color == 'w' else (22, 14, 8)
                    surface.blit(self.piece_font.render(character, True, piece_color), (screen_x + 2, screen_y))

        # Draw the piece being dragged at cursor position
        if dragging and drag_pos:
            cell = board[dragging[0]][dragging[1]]
            if cell:
                piece, color = cell
                character = UNICODE_PIECES[(piece, color)]
                cursor_x, cursor_y = drag_pos
                piece_color = (255, 255, 255) if color == 'w' else (22, 14, 8)
                surface.blit(self.piece_font.render(character, True, piece_color),
                             (cursor_x - lay.cell_size // 2 + 2, cursor_y - lay.cell_size // 2))

    def draw_status_bar(self, surface, turn, status, is_thinking, player_name, human_color):
        lay = self.layout
        human_label = "White" if human_color == 'w' else "Black"
        cpu_label = "Black" if human_color == 'w' else "White"

        if status == 'checkmate':
            if turn == human_color:
                message = "Checkmate! CPU wins  —  R to restart"
            else:
                message = f"Checkmate! {player_name} wins!  —  R to restart"
        elif status == 'stalemate':
            message = "Stalemate — Draw!  —  R to restart"
        elif status == 'forfeit':
            message = f"{player_name} forfeited  —  R to restart"
        elif is_thinking:
            message = "CPU is thinking…"
        elif status == 'check':
            if turn == human_color:
                message = f"Check!  —  {player_name}'s move"
            else:
                message = "Check!  —  CPU's move"
        else:
            if turn == human_color:
                message = f"{player_name}'s move  ({human_label})"
            else:
                message = f"CPU's move  ({cpu_label})"

        text = self.status_font.render(message, True, WHITE_TEXT)
        text_x = (lay.board_x + lay.board_size // 2) - text.get_width() // 2
        text_y = (lay.status_bar_height - text.get_height()) // 2
        surface.blit(text, (text_x, text_y))

    def draw_sidebar(self, surface, player_name, white_score, black_score, white_captures, black_captures, move_log, scroll, human_color='w'):
        lay = self.layout
        sidebar_x = lay.sidebar_x
        sidebar_y = lay.sidebar_y
        sidebar_w = lay.sidebar_width
        sidebar_h = lay.sidebar_height

        # Panel background
        pygame.draw.rect(surface, PANEL_BG, (sidebar_x, sidebar_y, sidebar_w, sidebar_h), border_radius=10)
        pygame.draw.rect(surface, PANEL_LINE, (sidebar_x, sidebar_y, sidebar_w, sidebar_h), 1, border_radius=10)

        current_y = sidebar_y + 14

        # --- SCORE SECTION ---
        score_header = self.header_font.render("SCORE", True, GOLD)
        surface.blit(score_header, (sidebar_x + sidebar_w // 2 - score_header.get_width() // 2, current_y))
        current_y += score_header.get_height() + 8

        bar_x = sidebar_x + 14
        bar_width = sidebar_w - 28
        bar_height = 32
        total_score = max(1, white_score + black_score)
        white_fraction = white_score / total_score

        # Background track
        pygame.draw.rect(surface, (40, 32, 24), (bar_x, current_y, bar_width, bar_height), border_radius=8)

        # White portion (left side)
        if white_score > 0:
            white_bar_width = max(1, int(bar_width * white_fraction))
            radius = 8 if black_score == 0 else 0
            pygame.draw.rect(surface, (225, 215, 195), (bar_x, current_y, white_bar_width, bar_height), border_radius=radius)
            pygame.draw.rect(surface, (225, 215, 195), (bar_x, current_y, min(8, white_bar_width), bar_height))
            pygame.draw.rect(surface, (225, 215, 195), (bar_x, current_y, white_bar_width, bar_height), border_radius=radius)

        # Black portion (right side)
        if black_score > 0:
            black_bar_width = bar_width - int(bar_width * white_fraction)
            black_bar_x = bar_x + int(bar_width * white_fraction)
            radius = 8 if white_score == 0 else 0
            pygame.draw.rect(surface, (55, 44, 33), (black_bar_x, current_y, black_bar_width, bar_height), border_radius=radius)

        # Bar outline
        pygame.draw.rect(surface, PANEL_LINE, (bar_x, current_y, bar_width, bar_height), 1, border_radius=8)

        # Score numbers
        white_score_text = self.big_font.render(str(white_score), True, BLACK_SCORE_TEXT)
        black_score_text = self.big_font.render(str(black_score), True, CPU_SCORE_TEXT)
        surface.blit(white_score_text, (bar_x + 6, current_y + bar_height // 2 - white_score_text.get_height() // 2))
        surface.blit(black_score_text, (bar_x + bar_width - black_score_text.get_width() - 6, current_y + bar_height // 2 - black_score_text.get_height() // 2))
        current_y += bar_height + 4

        # Score labels — use player name and correct color
        if human_color == 'w':
            left_label = self.small_font.render(f"{player_name} (White)", True, (170, 160, 145))
            right_label = self.small_font.render("CPU (Black)", True, (100, 88, 70))
        else:
            left_label = self.small_font.render("CPU (White)", True, (170, 160, 145))
            right_label = self.small_font.render(f"{player_name} (Black)", True, (100, 88, 70))
        surface.blit(left_label, (bar_x, current_y))
        surface.blit(right_label, (bar_x + bar_width - right_label.get_width(), current_y))
        current_y += left_label.get_height() + 12

        # --- CAPTURES SECTION ---
        pygame.draw.line(surface, PANEL_LINE, (sidebar_x + 10, current_y), (sidebar_x + sidebar_w - 10, current_y))
        current_y += 8

        captures_header = self.header_font.render("CAPTURES", True, GOLD)
        surface.blit(captures_header, (sidebar_x + sidebar_w // 2 - captures_header.get_width() // 2, current_y))
        current_y += captures_header.get_height() + 6

        # Player captured pieces
        if human_color == 'w':
            current_y = self.draw_capture_row(surface, white_captures, 'b', f"{player_name} captured:", current_y, sidebar_x, sidebar_w)
            current_y = self.draw_capture_row(surface, black_captures, 'w', "CPU captured:", current_y, sidebar_x, sidebar_w)
        else:
            current_y = self.draw_capture_row(surface, black_captures, 'w', f"{player_name} captured:", current_y, sidebar_x, sidebar_w)
            current_y = self.draw_capture_row(surface, white_captures, 'b', "CPU captured:", current_y, sidebar_x, sidebar_w)
        current_y += 4

        # --- MOVE LOG SECTION ---
        pygame.draw.line(surface, PANEL_LINE, (sidebar_x + 10, current_y), (sidebar_x + sidebar_w - 10, current_y))
        current_y += 8

        move_log_header = self.header_font.render("MOVE LOG", True, GOLD)
        surface.blit(move_log_header, (sidebar_x + sidebar_w // 2 - move_log_header.get_width() // 2, current_y))
        current_y += move_log_header.get_height() + 6

        scroll = self.draw_move_log(surface, move_log, scroll, current_y, sidebar_x, sidebar_y, sidebar_w, sidebar_h, human_color)
        return scroll

    def draw_capture_row(self, surface, pieces, show_as_color, label_text, current_y, sidebar_x, sidebar_w):
        # Sort captures by value (descending)
        sorted_pieces = sorted(pieces, key=lambda p: CAPTURE_ORDER.index(p) if p in CAPTURE_ORDER else 99)

        label = self.small_font.render(label_text, True, DIM_TEXT)
        surface.blit(label, (sidebar_x + 10, current_y))
        current_y += label.get_height() + 2

        draw_x = sidebar_x + 10
        for piece in sorted_pieces:
            character = UNICODE_PIECES[(piece, show_as_color)]
            piece_color = (240, 230, 215) if show_as_color == 'w' else (38, 28, 18)
            piece_image = self.capture_font.render(character, True, piece_color)
            # Wrap to next line if needed
            if draw_x + piece_image.get_width() > sidebar_x + sidebar_w - 10:
                draw_x = sidebar_x + 10
                current_y += piece_image.get_height() + 1
            surface.blit(piece_image, (draw_x, current_y))
            draw_x += piece_image.get_width() + 2

        return current_y + self.capture_font.get_height() + 6

    def draw_move_log(self, surface, move_log, scroll, log_top, sidebar_x, sidebar_y, sidebar_w, sidebar_h, human_color='w'):
        log_height = sidebar_y + sidebar_h - log_top - 10
        log_rect = pygame.Rect(sidebar_x + 6, log_top, sidebar_w - 12, log_height)

        row_height = self.mono_font.get_height() + 4
        total_rows = len(move_log)
        visible_rows = max(1, log_height // row_height)
        max_scroll = max(0, total_rows - visible_rows)
        scroll = max(0, min(scroll, max_scroll))

        old_clip = surface.get_clip()
        surface.set_clip(log_rect)

        for i in range(total_rows):
            row_y = log_top + (i - scroll) * row_height
            if row_y + row_height < log_top or row_y > log_top + log_height:
                continue

            entry = move_log[i]
            is_last_entry = (i == total_rows - 1)
            is_human_move = entry['color'] == human_color

            # Alternating row shade
            if i % 2 == 0:
                pygame.draw.rect(surface, (36, 28, 20), (sidebar_x + 6, row_y, sidebar_w - 12, row_height))

            # Move number
            number_text = self.mono_font.render(f"{entry['num']}.", True, DIM_TEXT)
            surface.blit(number_text, (sidebar_x + 10, row_y + 1))

            # Player tag — use player name for human moves
            tag = self.player_name if is_human_move else "CPU"
            tag_color = (200, 190, 170) if is_human_move else (120, 150, 200)
            player_text = self.mono_font.render(f"[{tag}]", True, tag_color)
            surface.blit(player_text, (sidebar_x + 10 + number_text.get_width() + 4, row_y + 1))

            # The move notation
            if is_last_entry and is_human_move:
                move_color = GOLD
            elif is_last_entry and not is_human_move:
                move_color = (140, 200, 255)
            else:
                move_color = WHITE_TEXT
            move_text = self.mono_font.render(entry['text'], True, move_color)
            surface.blit(move_text, (sidebar_x + 10 + number_text.get_width() + player_text.get_width() + 8, row_y + 1))

        surface.set_clip(old_clip)

        # Scroll hint
        if total_rows > visible_rows:
            hint = self.small_font.render("scroll ↑↓", True, (75, 60, 45))
            surface.blit(hint, (sidebar_x + sidebar_w - hint.get_width() - 8, sidebar_y + sidebar_h - hint.get_height() - 4))

        return scroll


# Main game loop and state management
class ChessGame:
    def __init__(self, screen, clock, layout, player_name, difficulty, player_color='w'):
        self.screen = screen
        self.clock = clock
        self.layout = layout
        self.player_name = player_name
        self.difficulty = difficulty
        self.human_color = player_color
        self.cpu_color = 'b' if player_color == 'w' else 'w'
        self.flipped = (player_color == 'b')

        self.chess_board = ChessBoard()
        self.ai = ChessAI(self.chess_board, depth=difficulty, color=self.cpu_color)
        self.renderer = ChessRenderer(self.layout, self.player_name, self.flipped)
        self.pause_menu = PauseMenu(self.screen, self.clock)

        self.move_counter = 0
        self.reset_game()

    def handle_resize(self, new_width, new_height):
        new_width = max(640, new_width)
        new_height = max(480, new_height)
        self.layout.recalculate(new_width, new_height)
        self.renderer.rebuild_fonts()
        self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

    def reset_game(self):
        self.move_counter = 0
        self.board = self.chess_board.create_board()
        self.turn = 'w'
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
        self.cpu_result = [None]
        self.cpu_thread = None
        self.white_score = 0
        self.black_score = 0
        self.white_captures = []
        self.black_captures = []
        self.move_log = []
        self.scroll = 0
        self.update_status()

        # If human plays Black, CPU (White) moves first
        if self.human_color == 'b':
            self.start_cpu_turn()

    def update_status(self):
        moves = self.chess_board.get_all_legal_moves(self.board, self.turn, self.last_move)
        if not moves:
            if self.chess_board.is_in_check(self.board, self.turn):
                self.status = 'checkmate'
                self.check_square = self.chess_board.find_king(self.board, self.turn)
            else:
                self.status = 'stalemate'
                self.check_square = None
        elif self.chess_board.is_in_check(self.board, self.turn):
            self.status = 'check'
            self.check_square = self.chess_board.find_king(self.board, self.turn)
        else:
            self.status = 'normal'
            self.check_square = None

    def commit_move(self, source, destination):
        piece = self.board[source[0]][source[1]][0]
        mover_color = self.board[source[0]][source[1]][1]
        captured_cell = self.board[destination[0]][destination[1]]

        # Check for en passant capture
        en_passant_capture = None
        if piece == 'P' and source[1] != destination[1] and captured_cell is None:
            en_passant_capture = self.board[source[0]][destination[1]]
        actual_capture = captured_cell or en_passant_capture

        is_castle_kingside = piece == 'K' and destination[1] - source[1] == 2
        is_castle_queenside = piece == 'K' and source[1] - destination[1] == 2
        is_promotion = piece == 'P' and (destination[0] == 0 or destination[0] == 7)

        # Apply the move
        self.last_move = (source, destination, piece)
        self.board = self.chess_board.apply_move(self.board, source[0], source[1], destination[0], destination[1])
        self.turn = 'b' if self.turn == 'w' else 'w'
        self.selected = None
        self.move_dots = []
        self.highlights = [source, destination]
        self.update_status()

        # Update captures and score
        if actual_capture:
            captured_piece = actual_capture[0]
            points = PIECE_SCORE.get(captured_piece, 0)
            if mover_color == 'w':
                self.white_score += points
                self.white_captures.append(captured_piece)
            else:
                self.black_score += points
                self.black_captures.append(captured_piece)

        # Add to move log
        self.move_counter += 1
        notation = self.chess_board.get_move_notation(piece, source, destination, is_castle_kingside, is_castle_queenside, is_promotion)
        self.move_log.append({'num': self.move_counter, 'color': mover_color, 'text': notation})

        # Auto-scroll to bottom
        self.scroll = len(self.move_log)

    def start_cpu_turn(self):
        self.cpu_thinking = True
        self.cpu_result = [None]
        thread = threading.Thread(target=self.ai.think, args=(self.board, self.last_move, self.cpu_result), daemon=True)
        thread.start()
        self.cpu_thread = thread

    def select_piece(self, row, col):
        if self.board[row][col] and self.board[row][col][1] == self.human_color:
            self.selected = (row, col)
            self.move_dots = self.chess_board.get_legal_moves(self.board, row, col, self.last_move)
        else:
            self.selected = None
            self.move_dots = []

    def try_human_move(self, row, col):
        if self.selected is None:
            return
        selected_row, selected_col = self.selected
        legal = self.chess_board.get_legal_moves(self.board, selected_row, selected_col, self.last_move)
        if (row, col) in legal:
            self.commit_move(self.selected, (row, col))
            self.cpu_highlights = []
            if self.turn == self.cpu_color and self.status not in ('checkmate', 'stalemate'):
                self.start_cpu_turn()
        else:
            self.select_piece(row, col)

    def show_pause_menu(self):
        # Draw current game state first so it shows behind the overlay
        self.draw()
        if self.human_color == 'w':
            player_score, cpu_score = self.white_score, self.black_score
        else:
            player_score, cpu_score = self.black_score, self.white_score
        result = self.pause_menu.run(self.player_name, player_score, cpu_score)
        if result == 'forfeit':
            self.cpu_thinking = False
            return 'main_menu'
        return 'resume'

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            elif event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.status not in ('checkmate', 'stalemate'):
                        result = self.show_pause_menu()
                        if result == 'main_menu':
                            return 'main_menu'
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_UP:
                    self.scroll = max(0, self.scroll - 1)
                elif event.key == pygame.K_DOWN:
                    self.scroll += 1

            elif event.type == pygame.MOUSEWHEEL:
                self.scroll = max(0, self.scroll - event.y)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.turn == self.human_color and not self.cpu_thinking and self.status not in ('checkmate', 'stalemate'):
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    square = self.renderer.screen_to_board(mouse_x, mouse_y)
                    if square:
                        row, col = square
                        if self.selected:
                            selected_row, selected_col = self.selected
                            legal = self.chess_board.get_legal_moves(self.board, selected_row, selected_col, self.last_move)
                            if (row, col) in legal:
                                self.try_human_move(row, col)
                            else:
                                self.select_piece(row, col)
                                if self.board[row][col] and self.board[row][col][1] == self.human_color:
                                    self.dragging = (row, col)
                        else:
                            self.select_piece(row, col)
                            if self.board[row][col] and self.board[row][col][1] == self.human_color:
                                self.dragging = (row, col)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    square = self.renderer.screen_to_board(mouse_x, mouse_y)
                    if square and self.status not in ('checkmate', 'stalemate'):
                        self.try_human_move(square[0], square[1])
                    self.dragging = None
                    self.drag_pos = None

        return 'continue'

    def draw(self):
        lay = self.layout
        self.screen.fill(BACKGROUND)

        # Status bar background
        pygame.draw.rect(self.screen, (28, 22, 16), (0, 0, lay.window_width, lay.status_bar_height))
        pygame.draw.line(self.screen, PANEL_LINE, (0, lay.status_bar_height), (lay.window_width, lay.status_bar_height))

        # Board border
        pygame.draw.rect(self.screen, BORDER_COLOR,
                         (lay.board_x - 5, lay.board_y - 5, lay.board_size + 10, lay.board_size + 10), 5, border_radius=4)

        # Board, labels, pieces
        self.renderer.draw_board(self.screen, self.selected, self.highlights,
                                 self.check_square, self.move_dots, self.cpu_highlights)
        self.renderer.draw_labels(self.screen)
        self.renderer.draw_pieces(self.screen, self.board, dragging=self.dragging, drag_pos=self.drag_pos)

        # Status bar text
        self.renderer.draw_status_bar(self.screen, self.turn, self.status, self.cpu_thinking, self.player_name, self.human_color)

        # Animated thinking dots
        if self.cpu_thinking:
            num_dots = pygame.time.get_ticks() // 400 % 4
            dots = '.' * num_dots
            dots_text = self.renderer.status_font.render(dots, True, (160, 140, 100))
            self.screen.blit(dots_text, (lay.board_x + lay.board_size // 2 + 140, (lay.status_bar_height - self.renderer.status_font.get_height()) // 2))

        # ESC/restart hint
        hint = self.renderer.label_font.render("ESC=menu  R=restart", True, (70, 55, 40))
        self.screen.blit(hint, (lay.board_x, lay.window_height - hint.get_height() - 6))

        # Sidebar
        self.scroll = self.renderer.draw_sidebar(self.screen, self.player_name, self.white_score, self.black_score,
                                                  self.white_captures, self.black_captures,
                                                  self.move_log, self.scroll, self.human_color)

        pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(FPS)

            # Update drag position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.dragging:
                self.drag_pos = (mouse_x, mouse_y)

            # Check if CPU finished thinking
            if self.cpu_thinking and self.cpu_result[0] is not None:
                self.cpu_thinking = False
                source, destination = self.cpu_result[0]
                self.commit_move(source, destination)
                self.cpu_highlights = [source, destination]

            # Handle input events
            result = self.handle_events()
            if result == 'quit':
                return 'quit'
            if result == 'main_menu':
                return 'main_menu'

            # Render everything
            self.draw()


def main():
    layout = Layout(int(SCREEN_WIDTH * 0.9), int(SCREEN_HEIGHT * 0.9))
    screen = pygame.display.set_mode((layout.window_width, layout.window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Chess vs CPU")
    clock = pygame.time.Clock()

    while True:
        # Show start menu
        start_menu = StartMenu(screen, clock)
        player_name, difficulty, player_color = start_menu.run()

        # Update screen reference in case it was resized during menu
        screen = pygame.display.get_surface()
        width, height = screen.get_size()
        layout.recalculate(width, height)

        # Start the game
        game = ChessGame(screen, clock, layout, player_name, difficulty, player_color)
        result = game.run()

        if result == 'quit':
            break
        # result == 'main_menu' loops back to start menu

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
