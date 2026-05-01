# Chess Profiles — Login, signup, and profile screens
# These menu screens let players create accounts and see their stats
# Reuses the UI helpers from chess_menus.py for consistency

import pygame
import sys

from chess_menus import (
    _draw_name_input, _draw_play_button, _draw_back_button,
    BACKGROUND, PANEL_BG, PANEL_LINE, GOLD, DIM_TEXT, WHITE_TEXT, FPS
)

# Red colour used for error messages
ERROR_RED = (220, 90, 90)


def _draw_password_input(screen, font, center_x, current_y, password_value, is_active, cursor_visible):
    #Just like _draw_name_input but shows asterisks instead of the actual characters
    #The real password is kept in a separate variable, only the display is masked
    masked = '*' * len(password_value)
    return _draw_name_input(screen, font, center_x, current_y, masked, is_active, cursor_visible)


def _draw_action_button(screen, font, center_x, current_y, label, color=(60, 140, 60), width=200, height=46):
    #Draws a generic action button (Log In, Sign Up, Play as Guest, Log Out, etc.)
    #Returns the rect so we can detect clicks on it
    btn_rect = pygame.Rect(center_x - width // 2, current_y, width, height)
    pygame.draw.rect(screen, color, btn_rect, border_radius=8)
    btn_text = font.render(label, True, (255, 255, 255))
    screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2,
                            btn_rect.centery - btn_text.get_height() // 2))
    return btn_rect


# Hub screen — shown when the player clicks "Profiles" from the main menu
class ProfileMenu:
    #If logged in, shows the user's stats and a "Log Out" button
    #If not logged in, shows "Log In" / "Sign Up" / "Play as Guest" buttons

    def __init__(self, screen, clock, db, logged_in_user=None):
        self.screen = screen
        self.clock = clock
        self.db = db
        self.logged_in_user = logged_in_user
        self.title_font = pygame.font.SysFont("georgia,serif", 48, bold=True)
        self.heading_font = pygame.font.SysFont("georgia,serif", 28, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.stat_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 22)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.buttons = {}  #Filled in by draw(), used by run() to detect clicks
        self.back_rect = None

    def run(self):
        #Main loop. Returns a dict like {'action': 'login'|'signup'|'guest'|'logout'|'back'}
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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return {'action': 'back'}
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.back_rect and self.back_rect.collidepoint(mouse_x, mouse_y):
                        return {'action': 'back'}
                    for action, btn_rect in self.buttons.items():
                        if btn_rect.collidepoint(mouse_x, mouse_y):
                            return {'action': action}

            self.draw(center_x, height)
            pygame.display.flip()

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        # Back button in top-left corner
        self.back_rect = _draw_back_button(self.screen, self.button_font, 20, 20)

        if self.logged_in_user:
            self._draw_logged_in(center_x, height)
        else:
            self._draw_logged_out(center_x, height)

    def _draw_logged_out(self, center_x, height):
        #Shows the three options when no one is logged in
        current_y = height // 2 - 200

        title = self.title_font.render("Profiles", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 50

        # Three stacked buttons
        self.buttons = {}
        self.buttons['login'] = _draw_action_button(
            self.screen, self.button_font, center_x, current_y, "Log In"
        )
        current_y += 60
        self.buttons['signup'] = _draw_action_button(
            self.screen, self.button_font, center_x, current_y, "Sign Up", color=(60, 100, 160)
        )
        current_y += 60
        self.buttons['guest'] = _draw_action_button(
            self.screen, self.button_font, center_x, current_y, "Play as Guest", color=(80, 80, 80)
        )

    def _draw_logged_in(self, center_x, height):
        #Shows the player's stats panel + Log Out button
        user = self.logged_in_user
        current_y = height // 2 - 240

        title = self.title_font.render("Profile", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 20

        username_text = self.heading_font.render(user['username'], True, WHITE_TEXT)
        self.screen.blit(username_text, (center_x - username_text.get_width() // 2, current_y))
        current_y += username_text.get_height() + 30

        # Stats panel
        panel_width = 400
        panel_height = 220
        panel_x = center_x - panel_width // 2
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, current_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(self.screen, PANEL_LINE, (panel_x, current_y, panel_width, panel_height), 1, border_radius=10)

        # Each line is "Label: Value"
        stats_y = current_y + 20
        line_height = 30
        stats = [
            ("Games played", user['games_played']),
            ("Wins", user['wins']),
            ("Losses", user['losses']),
            ("Draws", user['draws']),
            ("Current streak", user['current_streak']),
            ("Max streak", user['max_streak']),
        ]
        for label, value in stats:
            label_text = self.stat_font.render(label + ":", True, DIM_TEXT)
            value_text = self.stat_font.render(str(value), True, WHITE_TEXT)
            self.screen.blit(label_text, (panel_x + 30, stats_y))
            self.screen.blit(value_text, (panel_x + panel_width - value_text.get_width() - 30, stats_y))
            stats_y += line_height

        current_y += panel_height + 30

        # Log Out button
        self.buttons = {}
        self.buttons['logout'] = _draw_action_button(
            self.screen, self.button_font, center_x, current_y, "Log Out", color=(160, 60, 60)
        )


# Login screen — username + password
class LoginScreen:
    #Lets an existing user log in. Returns the user dict on success, or None if cancelled

    def __init__(self, screen, clock, db):
        self.screen = screen
        self.clock = clock
        self.db = db
        self.username = ""
        self.password = ""
        self.active_input = 'username'  #Which input field is currently focused
        self.error_message = None  #Shown in red below the inputs when login fails
        self.heading_font = pygame.font.SysFont("georgia,serif", 36, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.input_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 24)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.username_rect = None
        self.password_rect = None
        self.submit_rect = None
        self.back_rect = None

    def can_submit(self):
        #Both fields must be non-empty to attempt login
        return len(self.username.strip()) > 0 and len(self.password) > 0

    def _try_login(self):
        #Attempt to authenticate. Returns user dict on success, sets error_message on failure
        user = self.db.authenticate(self.username, self.password)
        if user is None:
            self.error_message = "Invalid username or password"
        return user

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
                    if event.key == pygame.K_RETURN and self.can_submit():
                        user = self._try_login()
                        if user:
                            return user
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_TAB:
                        #Tab cycles between username and password fields
                        self.active_input = 'password' if self.active_input == 'username' else 'username'
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_input == 'username':
                            self.username = self.username[:-1]
                        else:
                            self.password = self.password[:-1]
                    else:
                        if event.unicode.isprintable():
                            if self.active_input == 'username' and len(self.username) < 16:
                                self.username += event.unicode
                            elif self.active_input == 'password' and len(self.password) < 32:
                                self.password += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.username_rect and self.username_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'username'
                    elif self.password_rect and self.password_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'password'
                    elif self.back_rect and self.back_rect.collidepoint(mouse_x, mouse_y):
                        return None
                    elif self.submit_rect and self.submit_rect.collidepoint(mouse_x, mouse_y):
                        if self.can_submit():
                            user = self._try_login()
                            if user:
                                return user

            self.draw(center_x, height)
            pygame.display.flip()

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        self.back_rect = _draw_back_button(self.screen, self.button_font, 20, 20)

        current_y = height // 2 - 180

        # Title
        title = self.heading_font.render("Log In", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 30

        # Username input
        label = self.label_font.render("Username", True, WHITE_TEXT)
        self.screen.blit(label, (center_x - label.get_width() // 2, current_y))
        current_y += label.get_height() + 8
        self.username_rect = _draw_name_input(
            self.screen, self.input_font, center_x, current_y,
            self.username, self.active_input == 'username', self.cursor_visible
        )
        current_y += 44 + 20

        # Password input (masked with asterisks)
        label = self.label_font.render("Password", True, WHITE_TEXT)
        self.screen.blit(label, (center_x - label.get_width() // 2, current_y))
        current_y += label.get_height() + 8
        self.password_rect = _draw_password_input(
            self.screen, self.input_font, center_x, current_y,
            self.password, self.active_input == 'password', self.cursor_visible
        )
        current_y += 44 + 24

        # Error message (only shown if login failed)
        if self.error_message:
            err = self.label_font.render(self.error_message, True, ERROR_RED)
            self.screen.blit(err, (center_x - err.get_width() // 2, current_y))
            current_y += err.get_height() + 12
        else:
            current_y += 24  #Reserve space so the layout doesn't jump

        # Submit button
        self.submit_rect = _draw_play_button(self.screen, self.button_font, center_x, current_y, self.can_submit())
        current_y += 54 + 12

        # Hint
        hint = self.label_font.render("Tab to switch  |  Enter to submit  |  ESC to go back", True, DIM_TEXT)
        self.screen.blit(hint, (center_x - hint.get_width() // 2, current_y))


# Signup screen — username + password + confirm password
class SignupScreen:
    #Lets a new user create an account. Returns the user dict on success, or None if cancelled

    def __init__(self, screen, clock, db):
        self.screen = screen
        self.clock = clock
        self.db = db
        self.username = ""
        self.password = ""
        self.confirm = ""
        self.active_input = 'username'  #Cycles through username -> password -> confirm
        self.error_message = None
        self.heading_font = pygame.font.SysFont("georgia,serif", 36, bold=True)
        self.label_font = pygame.font.SysFont("georgia,serif", 22)
        self.input_font = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 24)
        self.button_font = pygame.font.SysFont("georgia,serif", 22, bold=True)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.username_rect = None
        self.password_rect = None
        self.confirm_rect = None
        self.submit_rect = None
        self.back_rect = None

    def can_submit(self):
        #All three fields must be non-empty to even attempt signup
        return (len(self.username.strip()) > 0 and len(self.password) > 0
                and len(self.confirm) > 0)

    def _validate(self):
        #Checks the inputs and returns an error message string, or None if everything looks good
        if not self.username.strip():
            return "Username cannot be empty"
        if len(self.password) < 4:
            return "Password must be at least 4 characters"
        if self.password != self.confirm:
            return "Passwords don't match"
        return None

    def _try_signup(self):
        #Validates inputs, creates the user, and returns the user dict on success
        error = self._validate()
        if error:
            self.error_message = error
            return None

        user = self.db.create_user(self.username, self.password)
        if user is None:
            self.error_message = "Username already taken"
        return user

    def _next_field(self):
        #Tab cycling order: username -> password -> confirm -> username
        order = ['username', 'password', 'confirm']
        idx = order.index(self.active_input)
        self.active_input = order[(idx + 1) % 3]

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
                    if event.key == pygame.K_RETURN and self.can_submit():
                        user = self._try_signup()
                        if user:
                            return user
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_TAB:
                        self._next_field()
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_input == 'username':
                            self.username = self.username[:-1]
                        elif self.active_input == 'password':
                            self.password = self.password[:-1]
                        else:
                            self.confirm = self.confirm[:-1]
                    else:
                        if event.unicode.isprintable():
                            if self.active_input == 'username' and len(self.username) < 16:
                                self.username += event.unicode
                            elif self.active_input == 'password' and len(self.password) < 32:
                                self.password += event.unicode
                            elif self.active_input == 'confirm' and len(self.confirm) < 32:
                                self.confirm += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.username_rect and self.username_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'username'
                    elif self.password_rect and self.password_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'password'
                    elif self.confirm_rect and self.confirm_rect.collidepoint(mouse_x, mouse_y):
                        self.active_input = 'confirm'
                    elif self.back_rect and self.back_rect.collidepoint(mouse_x, mouse_y):
                        return None
                    elif self.submit_rect and self.submit_rect.collidepoint(mouse_x, mouse_y):
                        if self.can_submit():
                            user = self._try_signup()
                            if user:
                                return user

            self.draw(center_x, height)
            pygame.display.flip()

    def draw(self, center_x, height):
        self.screen.fill(BACKGROUND)
        self.back_rect = _draw_back_button(self.screen, self.button_font, 20, 20)

        current_y = height // 2 - 240

        # Title
        title = self.heading_font.render("Sign Up", True, GOLD)
        self.screen.blit(title, (center_x - title.get_width() // 2, current_y))
        current_y += title.get_height() + 25

        # Username
        label = self.label_font.render("Username", True, WHITE_TEXT)
        self.screen.blit(label, (center_x - label.get_width() // 2, current_y))
        current_y += label.get_height() + 6
        self.username_rect = _draw_name_input(
            self.screen, self.input_font, center_x, current_y,
            self.username, self.active_input == 'username', self.cursor_visible
        )
        current_y += 44 + 14

        # Password
        label = self.label_font.render("Password", True, WHITE_TEXT)
        self.screen.blit(label, (center_x - label.get_width() // 2, current_y))
        current_y += label.get_height() + 6
        self.password_rect = _draw_password_input(
            self.screen, self.input_font, center_x, current_y,
            self.password, self.active_input == 'password', self.cursor_visible
        )
        current_y += 44 + 14

        # Confirm password
        label = self.label_font.render("Confirm Password", True, WHITE_TEXT)
        self.screen.blit(label, (center_x - label.get_width() // 2, current_y))
        current_y += label.get_height() + 6
        self.confirm_rect = _draw_password_input(
            self.screen, self.input_font, center_x, current_y,
            self.confirm, self.active_input == 'confirm', self.cursor_visible
        )
        current_y += 44 + 18

        # Error message
        if self.error_message:
            err = self.label_font.render(self.error_message, True, ERROR_RED)
            self.screen.blit(err, (center_x - err.get_width() // 2, current_y))
            current_y += err.get_height() + 8
        else:
            current_y += 20

        # Submit button
        self.submit_rect = _draw_play_button(self.screen, self.button_font, center_x, current_y, self.can_submit())
        current_y += 54 + 8

        # Hint
        hint = self.label_font.render("Tab to switch  |  Enter to submit  |  ESC to go back", True, DIM_TEXT)
        self.screen.blit(hint, (center_x - hint.get_width() // 2, current_y))
