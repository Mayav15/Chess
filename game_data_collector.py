# Game Data Collector — Silently records game data for future neural network training
# Every game (1P and 2P) saves board positions, moves, evaluations, and outcomes to JSON files

import json
import os
import uuid
from datetime import datetime

# Where game data files are stored (one JSON file per game)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game_data')


def _board_to_serializable(board):
    #Converts the 8x8 board (list of tuples/None) to a JSON-friendly format
    #Each cell becomes a 2-element list like ["P", "w"] or null
    result = []
    for row in board:
        serialized_row = []
        for cell in row:
            if cell is None:
                serialized_row.append(None)
            else:
                serialized_row.append([cell[0], cell[1]])  #(piece, color) -> [piece, color]
        result.append(serialized_row)
    return result


class GameDataCollector:
    #Records everything that happens during a chess game and saves it as a JSON file
    #This data will be used later to train a neural network

    def __init__(self, mode, difficulty=None):
        self.game_id = str(uuid.uuid4())
        self.mode = mode  #"cpu" or "2player"
        self.difficulty = difficulty  #1/2/3 for CPU games, None for 2P
        self.timestamp = datetime.now().isoformat()
        self.moves = []  #List of move records
        self.result = None  #Set when the game ends

    def record_move(self, board_before, color, source, destination, notation, evaluation=None):
        #Records a single move along with the board state before the move was made
        #evaluation is the minimax score (only available for CPU moves in 1P games)
        move_entry = {
            'move_number': len(self.moves) + 1,
            'color': color,
            'from': list(source),  #(row, col) -> [row, col]
            'to': list(destination),
            'board_before': _board_to_serializable(board_before),
            'evaluation': evaluation,
            'notation': notation,
        }
        self.moves.append(move_entry)

    def set_result(self, result):
        #Sets the game outcome: "white_win", "black_win", "draw", or "forfeit"
        self.result = result

    def save(self):
        #Writes the complete game record to a JSON file in the game_data folder
        #Creates the folder if it doesn't exist yet
        os.makedirs(DATA_DIR, exist_ok=True)

        game_record = {
            'game_id': self.game_id,
            'mode': self.mode,
            'difficulty': self.difficulty,
            'result': self.result,
            'timestamp': self.timestamp,
            'total_moves': len(self.moves),
            'moves': self.moves,
        }

        file_path = os.path.join(DATA_DIR, f'{self.game_id}.json')
        with open(file_path, 'w') as f:
            json.dump(game_record, f, indent=2)
