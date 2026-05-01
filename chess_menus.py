# Chess Menus — Start menus and pause menu
# This file has all the menu screens: mode selection, 1P/2P settings, and the in-game pause menu

import pygame
import sys

# Colours used across all menus (same palette as the game)
BACKGROUND = (20, 16, 12)
PANEL_BG = (30, 24, 18)
PANEL_LINE = (55, 44, 33)
GOLD = (212, 175, 55)
DIM_TEXT = (110, 90, 65)
WHITE_TEXT = (230, 220, 205)

FPS = 60

DIFFICULTY_LABELS = {1: "Easy", 2: "Medium", 3: "Hard"}
COLOR_LABELS = {'w': "White", 'b': "Black"}


def _draw_toggle_buttons(screen, font, center_x, current_y, items, selected_key, btn_width=140, btn_height=48, gap=20):
    #Draws a row of toggle buttons (like radio buttons) and returns a dict of {key: rect}
    #The selected button is filled gold, the rest are outlined
    total = btn_width * len(items) + gap * (len(items) - 1)
    start_x = center_x - total // 2
    rects = {}

    for i, (key, label) in enumerate(items):
        btn_x = start_x + i * (btn_width + gap)
        btn_rect = pygame.Rect(btn_x, current_y, btn_width, btn_height)
        rects[key] = btn_rect

        if selected_key == key:
            pygame.draw.rect(screen, GOLD, btn_rect, border_radius=8)
            text_color = (20, 16, 12)  #Dark text on gold background
        else:
            pygame.draw.rect(screen, (50, 40, 30), btn_rect, border_radius=8)
            pygame.draw.rect(screen, (90, 75, 55), btn_rect, 2, border_radius=8)  #Border only
            text_color = WHITE_TEXT

        btn_text = font.render(label, True, text_color)
        screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2,
                               btn_rect.centery - btn_text.get_height() // 2))

    return rects


def _draw_name_input(screen, font, center_x, current_y, name_value, is_active, cursor_visible):
    #Draws a text input box for entering player names
    #Shows a blinking cursor when the input is active
    input_width = 320
    input_height = 44
    input_rect = pygame.Rect(center_x - input_width // 2, current_y, input_width, input_height)

    pygame.draw.rect(screen, (40, 32, 24), input_rect, border_radius=6)
    border_color = GOLD if is_active else (90, 75, 55)  #Gold border when active/focused
    pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=6)

    display_name = name_value
    if is_active and cursor_visible:
        display_name += "|"  #Blinking cursor character
    name_text = font.render(display_name, True, WHITE_TEXT)
    screen.blit(name_text, (input_rect.x + 12, input_rect.y + input_height // 2 - name_text.get_height() // 2))

    return input_rect


def _draw_play_button(screen, font, center_x, current_y, can_play):
    #Draws the Play button — green when enabled, dimmed when name is empty
    play_width = 200
    play_height = 54
    play_rect = pygame.Rect(center_x - play_width // 2, current_y, play_width, play_height)

    if can_play:
        pygame.draw.rect(screen, (60, 140, 60), play_rect, border_radius=10)  #Green
        play_text = font.render("Play", True, (255, 255, 255))
    else:
        pygame.draw.rect(screen, (40, 32, 24), play_rect, border_radius=10)  #Dimmed
        pygame.draw.rect(screen, (60, 50, 35), play_rect, 2, border_radius=10)
        play_text = font.render("Play", True, DIM_TEXT)

    screen.blit(play_text, (play_rect.centerx - play_text.get_width() // 2,
                             play_rect.centery - play_text.get_height() // 2))
    return play_rect


def _draw_back_button(screen, font, x, y):
    #Draws a "< Back" button at the given position, returns its rect for click detection
    back_width = 100
    back_height = 40
    back_rect = pygame.Rect(x, y, back_width, back_height)
    pygame.draw.rect(screen, (50, 40, 30), back_rect, border_radius=8)
    pygame.draw.rect(screen, (90, 75, 55), back_rect, 2, border_radius=8)
    back_text = font.render("< Back", True, WHITE_TEXT)
    screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2,
                             back_rect.centery - back_text.get_height() // 2))
    return back_rect


# First screen — choose 1 Player, 2 Player, or open Profiles
class ModeMenu:
    #The main menu that appears when the game starts. Player picks 1P (vs CPU) or 2P (local)
    #Optionally shows the currently logged-in user, with a "Profiles" button to manage accounts

    def __init__(self, screen, clock, logged_in_user=None):
        self.screen = screen
        self.clock = clock
        self.logged_in_user = logged_in_user  #None for guest, otherwise dict from ProfileDB
        self.title_font = pygame.font.SysFont("georgia,serif", 64, bold=True)
        self.heading_font = pygame.font.SysFont("georgia,serif", 28, bold=True)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.small_font = pygame.font.SysFont("georgia,serif", 18)
        self.piece_font = pygame.font.SysFont("segoeuisymbol,symbola,freesans,dejavusans", 48)
        self.mode_buttons = {}
        self.profiles_button = None

    def run(self):
        #Main loop for the mode menu. Returns '1player', '2player', or 'profiles'
        while True:
            self.clock.tick(FPS)
            width = self.screen.get_width()
            height = self.screen.get_height()
            center_x = width // 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    for mode, btn_rect in self.mode_buttons.items():
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            return mode
                    if self.profiles_button and self.profiles_button.collidepoint(mouse_x, mouse_y):
                        return 'profiles'

            self.draw(center_x, height)
            pygame.display.flip()

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        current_y = height // 2 - 180

        # Title
        title = self.title_font.render("Chess", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 8

        # Decorative row of chess piece symbols
        pieces_text = "♟  ♝  ♞  ♜  ♛  ♔  ♜  ♞  ♝  ♟"
        pieces = self.piece_font.render(pieces_text, True, (120, 100, 75))
        self.screen.blit(pieces, (center_x - pieces.get_width() // 2, current_y))
        current_y += pieces.get_height() + 50

        # Mode selection buttons
        mode_label = self.heading_font.render("Select Game Mode", True, WHITE_TEXT)
        self.screen.blit(mode_label, (center_x - mode_label.get_width() // 2, current_y))
        current_y += mode_label.get_height() + 20

        self.mode_buttons = _draw_toggle_buttons(
            self.screen, self.button_font, center_x, current_y,
            [('1player', '1 Player'), ('2player', '2 Player')],
            None, btn_width=180, btn_height=56, gap=30
        )
        current_y += 56 + 30

        # Profiles button — secondary action below the mode buttons
        profile_width = 200
        profile_height = 44
        self.profiles_button = pygame.Rect(center_x - profile_width // 2, current_y, profile_width, profile_height)
        pygame.draw.rect(self.screen, (50, 40, 30), self.profiles_button, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, self.profiles_button, 2, border_radius=8)
        profile_text = self.button_font.render("Profiles", True, GOLD)
        self.screen.blit(profile_text, (self.profiles_button.centerx - profile_text.get_width() // 2,
                                          self.profiles_button.centery - profile_text.get_height() // 2))
        current_y += profile_height + 10

        # If someone is logged in, show their username in small gold text
        if self.logged_in_user:
            login_text = self.small_font.render(f"Logged in as: {self.logged_in_user['username']}", True, GOLD)
            self.screen.blit(login_text, (center_x - login_text.get_width() // 2, current_y))


# Second screen for 1 Player — name, difficulty, color
class SinglePlayerMenu:
    #Settings screen for 1 Player mode. Player enters their name, picks difficulty (1-3),
    #and chooses to play as White or Black. Returns a settings dict or None if they press back

    def __init__(self, screen, clock, default_name=""):
        self.screen = screen
        self.clock = clock
        self.player_name = default_name  #Pre-filled if a profile is logged in
        self.difficulty = 2  #Default to medium
        self.player_color = 'w'  #Default to white
        self.heading_font = pygame.font.SysFont("georgia,serif", 28, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.input_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 24)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.cursor_visible = True
        self.cursor_timer = 0  #Counter for blinking cursor animation
        self.diff_buttons = []
        self.color_buttons = {}
        self.play_rect = None
        self.back_rect = None

    def run(self):
        #Main loop for the settings screen. Returns settings dict on Play, or None on Back/ESC
        while True:
            self.clock.tick(FPS)
            # Blink the cursor every 30 frames (about half a second)
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0

            width = self.screen.get_width()
            height = self.screen.get_height()
            center_x = width // 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(self.player_name.strip()) > 0:
                        return self._build_result()  #Enter key starts the game
                    elif event.key == pygame.K_ESCAPE:
                        return None  #Go back to mode selection
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.key == pygame.K_1:
                        self.difficulty = 1
                    elif event.key == pygame.K_2:
                        self.difficulty = 2
                    elif event.key == pygame.K_3:
                        self.difficulty = 3
                    else:
                        # Only allow printable characters, max 16 chars, and don't type 1/2/3 into the name
                        if len(self.player_name) < 16 and event.unicode.isprintable() and event.unicode not in '123':
                            self.player_name += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    for i, btn_rect in enumerate(self.diff_buttons):
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            self.difficulty = i + 1
                    for color, btn_rect in self.color_buttons.items():
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            self.player_color = color
                    if self.back_rect and self.back_rect.collidepoint(mouse_x, mouse_y):
                        return None
                    if self.play_rect and self.play_rect.collidepoint(mouse_x, mouse_y):
                        if len(self.player_name.strip()) > 0:
                            return self._build_result()

            self.draw(center_x, height)
            pygame.display.flip()

    def _build_result(self):
        #Packages the player's settings into a dict for the game to use
        return {
            'mode': 'cpu',
            'player_name': self.player_name.strip(),
            'difficulty': self.difficulty,
            'player_color': self.player_color,
        }

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        current_y = height // 2 - 240

        # Back button (top-left corner)
        self.back_rect = _draw_back_button(self.screen, self.button_font, 20, 20)

        # Header
        header = self.heading_font.render("1 Player  —  vs CPU", True, GOLD)
        self.screen.blit(header, (center_x - header.get_width() // 2, current_y))
        current_y += header.get_height() + 30

        # Player name input
        name_label = self.heading_font.render("Player Name", True, WHITE_TEXT)
        self.screen.blit(name_label, (center_x - name_label.get_width() // 2, current_y))
        current_y += name_label.get_height() + 12

        _draw_name_input(self.screen, self.input_font, center_x, current_y,
                         self.player_name, True, self.cursor_visible)
        current_y += 44 + 30

        # Difficulty toggle buttons (Easy/Medium/Hard)
        diff_label = self.heading_font.render("Difficulty", True, WHITE_TEXT)
        self.screen.blit(diff_label, (center_x - diff_label.get_width() // 2, current_y))
        current_y += diff_label.get_height() + 12

        items = [(1, "Easy"), (2, "Medium"), (3, "Hard")]
        self.diff_buttons = list(_draw_toggle_buttons(
            self.screen, self.button_font, center_x, current_y,
            items, self.difficulty
        ).values())
        current_y += 48 + 12

        key_hint = self.label_font.render("or press 1 / 2 / 3", True, DIM_TEXT)
        self.screen.blit(key_hint, (center_x - key_hint.get_width() // 2, current_y))
        current_y += key_hint.get_height() + 24

        # Play as White or Black toggle
        color_label = self.heading_font.render("Play As", True, WHITE_TEXT)
        self.screen.blit(color_label, (center_x - color_label.get_width() // 2, current_y))
        current_y += color_label.get_height() + 12

        self.color_buttons = _draw_toggle_buttons(
            self.screen, self.button_font, center_x, current_y,
            [('w', "White"), ('b', "Black")], self.player_color
        )
        current_y += 48 + 30

        # Play button (only enabled when a name is entered)
        can_play = len(self.player_name.strip()) > 0
        self.play_rect = _draw_play_button(self.screen, self.button_font, center_x, current_y, can_play)
        current_y += 54 + 12

        # Keyboard shortcut hints
        enter_hint = self.label_font.render("Enter to play  |  ESC to go back", True, DIM_TEXT)
        self.screen.blit(enter_hint, (center_x - enter_hint.get_width() // 2, current_y))


# Second screen for 2 Player — Player 1 name (White) and Player 2 name (Black)
class TwoPlayerMenu:
    #Settings screen for 2 Player mode. Both players enter their names
    #Player 1 is always White, Player 2 is always Black. Tab switches between inputs

    def __init__(self, screen, clock, default_name=""):
        self.screen = screen
        self.clock = clock
        self.player1_name = default_name  #Pre-filled if a profile is logged in
        self.player2_name = ""
        self.active_input = 'player1'  #Which name input is currently focused
        self.heading_font = pygame.font.SysFont("georgia,serif", 28, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.input_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 24)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.name1_rect = None
        self.name2_rect = None
        self.play_rect = None
        self.back_rect = None

    def can_play(self):
        #Both players need to enter a name before the game can start
        return len(self.player1_name.strip()) > 0 and len(self.player2_name.strip()) > 0

    def run(self):
        #Main loop. Returns settings dict on Play, or None on Back/ESC
        while True:
            self.clock.tick(FPS)
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0

            width = self.screen.get_width()
            height = self.screen.get_height()
            center_x = width // 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.can_play():
                        return self._build_result()
                    elif event.key == pygame.K_ESCAPE:
                        return None  #Go back to mode selection
                    elif event.key == pygame.K_TAB:
                        #Tab switches focus between the two name inputs
                        self.active_input = 'player2' if self.active_input == 'player1' else 'player1'
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_input == 'player1':
                            self.player1_name = self.player1_name[:-1]
                        else:
                            self.player2_name = self.player2_name[:-1]
                    else:
                        if event.unicode.isprintable():
                            if self.active_input == 'player1' and len(self.player1_name) < 16:
                                self.player1_name += event.unicode
                            elif self.active_input == 'player2' and len(self.player2_name) < 16:
                                self.player2_name += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    #Click on an input box to focus it
                    if self.name1_rect and self.name1_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'player1'
                    if self.name2_rect and self.name2_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'player2'
                    if self.back_rect and self.back_rect.collidepoint(mouse_x, mouse_y):
                        return None
                    if self.play_rect and self.play_rect.collidepoint(mouse_x, mouse_y):
                        if self.can_play():
                            return self._build_result()

            self.draw(center_x, height)
            pygame.display.flip()

    def _build_result(self):
        #Packages the player names into a dict for the game to use
        return {
            'mode': '2player',
            'player_name': self.player1_name.strip(),
            'player2_name': self.player2_name.strip(),
        }

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        current_y = height // 2 - 180

        # Back button (top-left corner)
        self.back_rect = _draw_back_button(self.screen, self.button_font, 20, 20)

        # Header
        header = self.heading_font.render("2 Player  —  Local", True, GOLD)
        self.screen.blit(header, (center_x - header.get_width() // 2, current_y))
        current_y += header.get_height() + 30

        # Player 1 (White) name input
        p1_label = self.heading_font.render("Player 1 (White)", True, WHITE_TEXT)
        self.screen.blit(p1_label, (center_x - p1_label.get_width() // 2, current_y))
        current_y += p1_label.get_height() + 12

        self.name1_rect = _draw_name_input(self.screen, self.input_font, center_x, current_y,
                                            self.player1_name, self.active_input == 'player1',
                                            self.cursor_visible)
        current_y += 44 + 24

        # Player 2 (Black) name input
        p2_label = self.heading_font.render("Player 2 (Black)", True, WHITE_TEXT)
        self.screen.blit(p2_label, (center_x - p2_label.get_width() // 2, current_y))
        current_y += p2_label.get_height() + 12

        self.name2_rect = _draw_name_input(self.screen, self.input_font, center_x, current_y,
                                            self.player2_name, self.active_input == 'player2',
                                            self.cursor_visible)
        current_y += 44 + 30

        # Play button (only enabled when both names are entered)
        self.play_rect = _draw_play_button(self.screen, self.button_font, center_x, current_y, self.can_play())
        current_y += 54 + 12

        # Keyboard shortcut hints
        hints = self.label_font.render("Tab to switch  |  Enter to play  |  ESC to go back", True, DIM_TEXT)
        self.screen.blit(hints, (center_x - hints.get_width() // 2, current_y))


# Pause menu — shown when ESC is pressed during the game
class PauseMenu:
    #Overlay that appears on top of the game when you press ESC
    #Shows the score and lets you resume or forfeit/quit

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.heading_font = pygame.font.SysFont("georgia,serif", 36, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.score_font = pygame.font.SysFont("georgia,serif", 26, bold=True)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)

    def run(self, white_label, black_label, white_score, black_score, two_player=False):
        #Returns 'resume', 'quit' (2P), or 'forfeit' (1P)
        #We save a snapshot of the game screen so we can draw the game behind the overlay
        self.game_snapshot = self.screen.copy()

        while True:
            self.clock.tick(FPS)
            width = self.screen.get_width()
            height = self.screen.get_height()
            center_x = width // 2
            center_y = height // 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'resume'  #ESC again to go back to the game
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if hasattr(self, 'resume_rect') and self.resume_rect.collidepoint(mouse_x, mouse_y):
                        return 'resume'
                    if hasattr(self, 'exit_rect') and self.exit_rect.collidepoint(mouse_x, mouse_y):
                        return 'quit' if two_player else 'forfeit'

            self.draw(center_x, center_y, white_label, black_label, white_score, black_score, two_player)
            pygame.display.flip()

    def draw(self, center_x, center_y, white_label, black_label, white_score, black_score, two_player=False):
        # Restore the game frame first, then darken it with a semi-transparent overlay
        # Without restoring the snapshot each frame, the overlay would stack and get darker and darker
        if hasattr(self, 'game_snapshot'):
            self.screen.blit(self.game_snapshot, (0, 0))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        #SRCALPHA lets us use transparency in the fill color
        overlay.fill((0, 0, 0, 160))  #Black with 160/255 opacity
        self.screen.blit(overlay, (0, 0))

        # Centered panel box
        panel_width = 400
        panel_height = 320
        panel_x = center_x - panel_width // 2
        panel_y = center_y - panel_height // 2
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, panel_y, panel_width, panel_height), border_radius=14)
        pygame.draw.rect(self.screen, GOLD, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=14)

        current_y = panel_y + 24

        # Title
        title = self.heading_font.render("Game Paused", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 20

        # Divider line
        pygame.draw.line(self.screen, PANEL_LINE, (panel_x + 20, current_y), (panel_x + panel_width - 20, current_y))
        current_y += 16

        # Score display
        score_label = self.label_font.render("Current Score", True, WHITE_TEXT)
        self.screen.blit(score_label, (center_x - score_label.get_width() // 2, current_y))
        current_y += score_label.get_height() + 10

        white_text = self.score_font.render(f"{white_label}: {white_score}", True, (225, 215, 195))
        self.screen.blit(white_text, (center_x - white_text.get_width() // 2, current_y))
        current_y += white_text.get_height() + 4

        black_text = self.score_font.render(f"{black_label}: {black_score}", True, (120, 150, 200))
        self.screen.blit(black_text, (center_x - black_text.get_width() // 2, current_y))
        current_y += black_text.get_height() + 24

        # Action buttons side by side
        button_width = 160
        button_height = 46
        button_gap = 24

        # Resume button (green, left side)
        resume_x = center_x - button_width - button_gap // 2
        self.resume_rect = pygame.Rect(resume_x, current_y, button_width, button_height)
        pygame.draw.rect(self.screen, (60, 140, 60), self.resume_rect, border_radius=8)
        resume_text = self.button_font.render("Resume", True, (255, 255, 255))
        self.screen.blit(resume_text, (self.resume_rect.centerx - resume_text.get_width() // 2,
                                        self.resume_rect.centery - resume_text.get_height() // 2))

        # Forfeit / Quit button (red, right side)
        # In 2 player mode it says "Quit", in 1 player mode it says "Forfeit"
        exit_x = center_x + button_gap // 2
        self.exit_rect = pygame.Rect(exit_x, current_y, button_width, button_height)
        pygame.draw.rect(self.screen, (160, 50, 50), self.exit_rect, border_radius=8)
        exit_label = "Quit" if two_player else "Forfeit"
        exit_text = self.button_font.render(exit_label, True, (255, 255, 255))
        self.screen.blit(exit_text, (self.exit_rect.centerx - exit_text.get_width() // 2,
                                      self.exit_rect.centery - exit_text.get_height() // 2))

        current_y += button_height + 14
        hint = self.label_font.render("ESC to resume", True, DIM_TEXT)
        self.screen.blit(hint, (center_x - hint.get_width() // 2, current_y))
