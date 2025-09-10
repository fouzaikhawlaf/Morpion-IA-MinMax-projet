from flask import Flask, request, jsonify
from flask_cors import CORS
import math

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])  # Autoriser les deux ports

# Plateau de jeu global (9 cases vides au départ)
board = [" " for _ in range(9)]
# Historique des parties
game_history = []
# Niveau de difficulté (par défaut difficile)
difficulty = "hard"

def available_moves(board):
    return [i for i, spot in enumerate(board) if spot == " "]

def winner(board):
    win_combos = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for combo in win_combos:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != " ":
            return board[combo[0]]
    return None

def minimax(board, depth, is_maximizing, alpha=-math.inf, beta=math.inf, max_depth=math.inf):
    win = winner(board)
    if win == "O": return 1
    if win == "X": return -1
    if " " not in board: return 0
    if depth >= max_depth: return 0  # Limite de profondeur pour les niveaux faciles

    if is_maximizing:
        best_score = -math.inf
        for move in available_moves(board):
            board[move] = "O"
            score = minimax(board, depth+1, False, alpha, beta, max_depth)
            board[move] = " "
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = math.inf
        for move in available_moves(board):
            board[move] = "X"
            score = minimax(board, depth+1, True, alpha, beta, max_depth)
            board[move] = " "
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score

def best_move(board, difficulty="hard"):
    best_score = -math.inf
    move = None
    max_depth = math.inf
    if difficulty == "easy":
        max_depth = 2  # Profondeur limitée pour le niveau facile
    elif difficulty == "medium":
        max_depth = 4  # Profondeur moyenne

    for i in available_moves(board):
        board[i] = "O"
        score = minimax(board, 0, False, max_depth=max_depth)
        board[i] = " "
        if score > best_score:
            best_score = score
            move = i
    return move

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Backend Morpion opérationnel ✅"})

@app.route("/move", methods=["POST"])
def move():
    global board, game_history
    data = request.get_json()
    
    if not data or "move" not in data:
        return jsonify({"error": "Données manquantes"}), 400
        
    player_move = data["move"]

    if board[player_move] != " ":
        return jsonify({"error": "Case occupée"}), 400

    # Sauvegarde de l'état avant le coup du joueur
    previous_board = board.copy()
    board[player_move] = "X"
    
    win = winner(board)
    if win or " " not in board:
        game_history.append({
            "board": board.copy(),
            "winner": win,
            "player_move": player_move,
            "ia_move": None
        })
        return jsonify({"board": board, "winner": win})

    ia_move = best_move(board, difficulty)
    board[ia_move] = "O"

    win = winner(board)
    # Sauvegarde de l'état après le coup de l'IA
    game_history.append({
        "board": board.copy(),
        "winner": win,
        "player_move": player_move,
        "ia_move": ia_move
    })
    return jsonify({"board": board, "winner": win, "ia_move": ia_move})

@app.route("/reset", methods=["POST"])
def reset():
    global board
    board = [" " for _ in range(9)]
    return jsonify({"board": board})

@app.route("/history", methods=["GET"])
def get_history():
    return jsonify({"history": game_history})

@app.route("/difficulty", methods=["POST"])
def set_difficulty():
    global difficulty
    data = request.get_json()
    if not data or "difficulty" not in data:
        return jsonify({"error": "Données manquantes"}), 400
    difficulty = data["difficulty"]
    return jsonify({"difficulty": difficulty})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)