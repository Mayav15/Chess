# Chess

A chess game built with Python and Pygame. Play against a CPU opponent powered by minimax AI with alpha-beta pruning, or play locally with a friend. Optionally create a player profile to track your wins, losses, draws, and streaks.

## Screenshots

### Main Menu

| Logged Out | Logged In |
|------------|-----------|
| ![Main Menu](screenshots/mode_menu.png) | ![Main Menu Logged In](screenshots/mode_menu_logged_in.png) |

### Profile System

| Profiles (Logged Out) | Log In | Sign Up | Profile Stats |
|---------------------|--------|---------|---------------|
| ![Profile Menu](screenshots/profile_menu.png) | ![Login](screenshots/login_screen.png) | ![Signup](screenshots/signup_screen.png) | ![Profile Stats](screenshots/profile_logged_in.png) |

### Game Settings

| 1 Player Settings | 2 Player Settings |
|-------------------|-------------------|
| ![1P Settings](screenshots/1p_settings.png) | ![2P Settings](screenshots/2p_settings.png) |

### 1 Player — Playing as White

| Opening | Mid-Game | Checkmate |
|---------|----------|-----------|
| ![White Opening](screenshots/white_opening.png) | ![White Mid-Game](screenshots/white_midgame.png) | ![White Checkmate](screenshots/white_checkmate.png) |

### 1 Player — Playing as Black

| Opening | Mid-Game | Checkmate |
|---------|----------|-----------|
| ![Black Opening](screenshots/black_opening.png) | ![Black Mid-Game](screenshots/black_midgame.png) | ![Black Checkmate](screenshots/black_checkmate.png) |

### 2 Player — Local Game

![2P Mid-Game](screenshots/2p_midgame.png)

### Pause Menus

| 1 Player (Forfeit) | 2 Player (Quit) |
|---------------------|-----------------|
| ![1P Pause](screenshots/1p_pause.png) | ![2P Pause](screenshots/2p_pause.png) |

## Features

- **1 Player or 2 Player** -- Play against the CPU or locally with a friend
- **Player Profiles** -- Optional accounts with username/password (passwords hashed with PBKDF2-SHA256). Tracks games played, wins/losses/draws, current streak, and max streak.
- **Difficulty levels** -- Easy, Medium, and Hard (minimax search depth 1, 2, or 3)
- **Play as White or Black** -- Choose which side to play in 1 Player mode; the board flips accordingly
- **Drag & drop or click** -- Move pieces by clicking or dragging them
- **Move validation** -- Full chess rules including castling, en passant, and pawn promotion
- **Draw detection** -- Stalemate, repeated moves, and kings-only positions automatically end as draws
- **Visual feedback** -- Highlighted legal moves, last move indicators, check warnings, and CPU move highlights
- **Sidebar panel** -- Live score bar, captured pieces display, and scrollable move log
- **Pause menu** -- Press ESC to pause, view the score, and choose to resume, forfeit (1P), or quit (2P)
- **Resizable window** -- Minimize, maximize, or resize the window freely
- **Unicode pieces** -- Clean rendering using Unicode chess symbols

## Controls

| Key | Action |
|-----|--------|
| Click / Drag | Select and move pieces |
| `ESC` | Pause menu / go back / exit finished game |
| `1` / `2` / `3` | Select difficulty (1 Player settings) |
| `Tab` | Switch input field (settings and login/signup screens) |
| Scroll / Arrow keys | Scroll move log |

## File Structure

| File | Description |
|------|-------------|
| `chess_game.py` | Main game loop, rendering, and entry point |
| `chess_ai.py` | Board logic and minimax AI with alpha-beta pruning |
| `chess_menus.py` | Menus (mode selection, settings, pause) |
| `chess_profiles.py` | Profile screens (login, signup, profile stats) |
| `chess_db.py` | SQLite database layer for player accounts |

## Requirements

- Python 3.x
- Pygame

## Running

```bash
pip install pygame
python chess_game.py
```
