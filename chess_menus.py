# Chess Menus — Start menu and pause menu

import pygame
import sys

# Colours (shared with chess_game)
BACKGROUND = (20, 16, 12)
PANEL_BG = (30, 24, 18)
PANEL_LINE = (55, 44, 33)
GOLD = (212, 175, 55)
DIM_TEXT = (110, 90, 65)
WHITE_TEXT = (230, 220, 205)

FPS = 60

DIFFICULTY_LABELS = {1: "Easy", 2: "Medium", 3: "Hard"}
COLOR_LABELS = {'w': "White", 'b': "Black"}


# Start menu — difficulty selection, color selection, and player name input
class StartMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.player_name = ""
        self.difficulty = 2
        self.player_color = 'w'
        self.title_font = pygame.font.SysFont("georgia,serif", 64, bold=True)
        self.heading_font = pygame.font.SysFont("georgia,serif", 28, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.input_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 24)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.piece_font = pygame.font.SysFont("segoeuisymbol,symbola,freesans,dejavusans", 48)
        self.name_active = True
        self.cursor_visible = True
        self.cursor_timer = 0

    def run(self):
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
                    if event.key == pygame.K_RETURN and len(self.player_name.strip()) > 0:
                        return self.player_name.strip(), self.difficulty, self.player_color
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.key == pygame.K_1:
                        self.difficulty = 1
                    elif event.key == pygame.K_2:
                        self.difficulty = 2
                    elif event.key == pygame.K_3:
                        self.difficulty = 3
                    else:
                        if len(self.player_name) < 16 and event.unicode.isprintable() and event.unicode not in '123':
                            self.player_name += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Check difficulty buttons
                    for i, btn_rect in enumerate(self.diff_buttons):
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            self.difficulty = i + 1
                    # Check color buttons
                    for color, btn_rect in self.color_buttons.items():
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            self.player_color = color
                    # Check play button
                    if hasattr(self, 'play_rect') and self.play_rect.collidepoint(mouse_x, mouse_y):
                        if len(self.player_name.strip()) > 0:
                            return self.player_name.strip(), self.difficulty, self.player_color

            self.draw(center_x, height)
            pygame.display.flip()

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        current_y = height // 2 - 280

        # Title
        title = self.title_font.render("Chess", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 8

        # Decorative pieces
        pieces_text = "♟  ♝  ♞  ♜  ♛  ♔  ♜  ♞  ♝  ♟"
        pieces = self.piece_font.render(pieces_text, True, (120, 100, 75))
        self.screen.blit(pieces, (center_x - pieces.get_width() // 2, current_y))
        current_y += pieces.get_height() + 40

        # Player name section
        name_label = self.heading_font.render("Player Name", True, WHITE_TEXT)
        self.screen.blit(name_label, (center_x - name_label.get_width() // 2, current_y))
        current_y += name_label.get_height() + 12

        # Name input box
        input_width = 320
        input_height = 44
        input_rect = pygame.Rect(center_x - input_width // 2, current_y, input_width, input_height)
        pygame.draw.rect(self.screen, (40, 32, 24), input_rect, border_radius=6)
        pygame.draw.rect(self.screen, GOLD, input_rect, 2, border_radius=6)

        display_name = self.player_name
        if self.cursor_visible:
            display_name += "|"
        name_text = self.input_font.render(display_name, True, WHITE_TEXT)
        self.screen.blit(name_text, (input_rect.x + 12, input_rect.y + input_height // 2 - name_text.get_height() // 2))
        current_y += input_height + 30

        # Difficulty section
        diff_label = self.heading_font.render("Difficulty", True, WHITE_TEXT)
        self.screen.blit(diff_label, (center_x - diff_label.get_width() // 2, current_y))
        current_y += diff_label.get_height() + 12

        # Difficulty buttons
        button_width = 140
        button_height = 48
        button_gap = 20
        total_width = button_width * 3 + button_gap * 2
        start_x = center_x - total_width // 2

        self.diff_buttons = []
        for i in range(3):
            level = i + 1
            btn_x = start_x + i * (button_width + button_gap)
            btn_rect = pygame.Rect(btn_x, current_y, button_width, button_height)
            self.diff_buttons.append(btn_rect)

            is_selected = (self.difficulty == level)
            if is_selected:
                pygame.draw.rect(self.screen, GOLD, btn_rect, border_radius=8)
                text_color = (20, 16, 12)
            else:
                pygame.draw.rect(self.screen, (50, 40, 30), btn_rect, border_radius=8)
                pygame.draw.rect(self.screen, (90, 75, 55), btn_rect, 2, border_radius=8)
                text_color = WHITE_TEXT

            btn_text = self.button_font.render(DIFFICULTY_LABELS[level], True, text_color)
            self.screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2,
                                        btn_rect.centery - btn_text.get_height() // 2))

        current_y += button_height + 12
        key_hint = self.label_font.render("or press 1 / 2 / 3", True, DIM_TEXT)
        self.screen.blit(key_hint, (center_x - key_hint.get_width() // 2, current_y))
        current_y += key_hint.get_height() + 30

        # Play as section
        color_label = self.heading_font.render("Play As", True, WHITE_TEXT)
        self.screen.blit(color_label, (center_x - color_label.get_width() // 2, current_y))
        current_y += color_label.get_height() + 12

        color_button_width = 140
        color_button_height = 48
        color_gap = 20
        color_total = color_button_width * 2 + color_gap
        color_start_x = center_x - color_total // 2

        self.color_buttons = {}
        for i, color_key in enumerate(['w', 'b']):
            btn_x = color_start_x + i * (color_button_width + color_gap)
            btn_rect = pygame.Rect(btn_x, current_y, color_button_width, color_button_height)
            self.color_buttons[color_key] = btn_rect

            is_selected = (self.player_color == color_key)
            if is_selected:
                pygame.draw.rect(self.screen, GOLD, btn_rect, border_radius=8)
                text_color = (20, 16, 12)
            else:
                pygame.draw.rect(self.screen, (50, 40, 30), btn_rect, border_radius=8)
                pygame.draw.rect(self.screen, (90, 75, 55), btn_rect, 2, border_radius=8)
                text_color = WHITE_TEXT

            btn_text = self.button_font.render(COLOR_LABELS[color_key], True, text_color)
            self.screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2,
                                        btn_rect.centery - btn_text.get_height() // 2))

        current_y += color_button_height + 30

        # Play button
        play_width = 200
        play_height = 54
        self.play_rect = pygame.Rect(center_x - play_width // 2, current_y, play_width, play_height)
        can_play = len(self.player_name.strip()) > 0

        if can_play:
            pygame.draw.rect(self.screen, (60, 140, 60), self.play_rect, border_radius=10)
            play_text = self.button_font.render("Play", True, (255, 255, 255))
        else:
            pygame.draw.rect(self.screen, (40, 32, 24), self.play_rect, border_radius=10)
            pygame.draw.rect(self.screen, (60, 50, 35), self.play_rect, 2, border_radius=10)
            play_text = self.button_font.render("Play", True, DIM_TEXT)

        self.screen.blit(play_text, (self.play_rect.centerx - play_text.get_width() // 2,
                                      self.play_rect.centery - play_text.get_height() // 2))
        current_y += play_height + 12

        enter_hint = self.label_font.render("or press Enter", True, DIM_TEXT)
        self.screen.blit(enter_hint, (center_x - enter_hint.get_width() // 2, current_y))


# Pause menu — shown when ESC is pressed during the game
class PauseMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.heading_font = pygame.font.SysFont("georgia,serif", 36, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.score_font = pygame.font.SysFont("georgia,serif", 26, bold=True)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)

    def run(self, player_name, white_score, black_score):
        # Returns 'resume' or 'forfeit'
        # Capture the current game frame so we can redraw it behind the overlay each frame
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
                        return 'resume'

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if hasattr(self, 'resume_rect') and self.resume_rect.collidepoint(mouse_x, mouse_y):
                        return 'resume'
                    if hasattr(self, 'forfeit_rect') and self.forfeit_rect.collidepoint(mouse_x, mouse_y):
                        return 'forfeit'

            self.draw(center_x, center_y, player_name, white_score, black_score)
            pygame.display.flip()

    def draw(self, center_x, center_y, player_name, white_score, black_score):
        # Restore the game frame, then darken it with a semi-transparent overlay
        if hasattr(self, 'game_snapshot'):
            self.screen.blit(self.game_snapshot, (0, 0))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Panel
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

        # Divider
        pygame.draw.line(self.screen, PANEL_LINE, (panel_x + 20, current_y), (panel_x + panel_width - 20, current_y))
        current_y += 16

        # Score display
        score_label = self.label_font.render("Current Score", True, WHITE_TEXT)
        self.screen.blit(score_label, (center_x - score_label.get_width() // 2, current_y))
        current_y += score_label.get_height() + 10

        player_score = self.score_font.render(f"{player_name}: {white_score}", True, (225, 215, 195))
        self.screen.blit(player_score, (center_x - player_score.get_width() // 2, current_y))
        current_y += player_score.get_height() + 4

        cpu_score = self.score_font.render(f"CPU: {black_score}", True, (120, 150, 200))
        self.screen.blit(cpu_score, (center_x - cpu_score.get_width() // 2, current_y))
        current_y += cpu_score.get_height() + 24

        # Buttons
        button_width = 160
        button_height = 46
        button_gap = 24

        # Resume button
        resume_x = center_x - button_width - button_gap // 2
        self.resume_rect = pygame.Rect(resume_x, current_y, button_width, button_height)
        pygame.draw.rect(self.screen, (60, 140, 60), self.resume_rect, border_radius=8)
        resume_text = self.button_font.render("Resume", True, (255, 255, 255))
        self.screen.blit(resume_text, (self.resume_rect.centerx - resume_text.get_width() // 2,
                                        self.resume_rect.centery - resume_text.get_height() // 2))

        # Forfeit button
        forfeit_x = center_x + button_gap // 2
        self.forfeit_rect = pygame.Rect(forfeit_x, current_y, button_width, button_height)
        pygame.draw.rect(self.screen, (160, 50, 50), self.forfeit_rect, border_radius=8)
        forfeit_text = self.button_font.render("Forfeit", True, (255, 255, 255))
        self.screen.blit(forfeit_text, (self.forfeit_rect.centerx - forfeit_text.get_width() // 2,
                                         self.forfeit_rect.centery - forfeit_text.get_height() // 2))

        current_y += button_height + 14
        hint = self.label_font.render("ESC to resume", True, DIM_TEXT)
        self.screen.blit(hint, (center_x - hint.get_width() // 2, current_y))
