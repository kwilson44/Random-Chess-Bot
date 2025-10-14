import chess
from datetime import datetime
import random
import sys

class ChessGameError(Exception):
    """Custom exception for chess game errors"""
    pass

# piece values based on what the chess experts say lol
PIECE_VALUES = {
    chess.PAWN: 100,    # Base 1.0
    chess.KNIGHT: 320,  # Base 3.2
    chess.BISHOP: 330,  # Base 3.3
    chess.ROOK: 500,    # Base 5.0
    chess.QUEEN: 900,   # Base 9.0
    chess.KING: 20000   # High value to prioritize king safety
}

CENTER_SQUARES = [chess.E4, chess.E5, chess.D4, chess.D5]

def order_moves(board, moves):
    """Order moves for better alpha-beta pruning efficiency"""
    def move_score(move):
        score = 0
        # Prioritize captures
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            if captured:
                score += PIECE_VALUES[captured.piece_type]
        # Prioritize center control        
        if move.to_square in CENTER_SQUARES:
            score += 50
        return score
    
    return sorted(moves, key=move_score, reverse=True)

CHECKMATE_SCORE = 1000
STALEMATE_SCORE = 0

def print_header():
    print("=====================================================")
    print("             CS 290 Chess Bot Version 0.2")
    print("                  With Minimax!")
    print("=====================================================")
    print(f"Time: {datetime.now()}")

def get_player_move(board):
    while True:
        try:
            user_move = input("Your move (or 'quit' to end, 'help' for commands): ").strip().lower()
            
            if user_move == "quit":
                return None
            if user_move == "help":
                print("\nCommands:")
                print("- Enter moves in UCI format (like e2e4)")
                print("- For pawn promotion, add q/r/b/n (like c7b8q for Queen)")
                print("  q=Queen, r=Rook, b=Bishop, n=Knight")
                print("- 'quit' to end the game")
                print("- 'legal' to see all legal moves")
                print("- 'fen' to see current FEN")
                continue
            if user_move == "legal":
                print("Legal moves:", " ".join(move.uci() for move in board.legal_moves))
                continue
            if user_move == "fen":
                print("Current FEN:", board.fen())
                continue
                
            move = validate_move(board, user_move)
            return move
            
        except ChessGameError as e:
            print(f"Error: {str(e)}")
        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
            sys.exit(0)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

def get_computer_color():
    while True:
        color = input("Computer Player? (w=white/b=black): ").strip().lower()
        if color in ('w', 'b'):
            return color
        print("Invalid input. Enter 'w' for white or 'b' for black")

def validate_fen(fen):
    if not fen:
        return None
        
    try:
        parts = fen.split()
        if len(parts) != 6:
            raise ChessGameError("FEN must have 6 space-separated fields")
            
        rows = parts[0].split('/')
        if len(rows) != 8:
            raise ChessGameError("FEN must have 8 ranks separated by '/'")
            
        try:
            board = chess.Board(fen)
            return board
        except ValueError as e:
            raise ChessGameError(f"Invalid FEN format: {str(e)}")
            
    except Exception as e:
        raise ChessGameError(f"Invalid FEN: {str(e)}")

def validate_move(board, move_str):
    """Validates a move with detailed error checking (supports promotions)."""
    try:
        # UCI moves are length 4, promotions length 5 (like for example e7e8q)
        if len(move_str) not in (4, 5):
            raise ChessGameError("Move must be 4 chars (like e2e4) or 5 for promotion (e7e8q)")
        
        base = move_str[:4]
        if not all(c in 'abcdefgh12345678' for c in base):
            raise ChessGameError("Invalid characters in move. Use algebraic notation (a-h, 1-8)")
        
        # If promotion, validate promotion piece
        if len(move_str) == 5:
            if move_str[4] not in 'qrbn':
                raise ChessGameError("Invalid promotion piece. Use one of q/r/b/n")
        
        move = chess.Move.from_uci(move_str)
        
        if move not in board.legal_moves:
            if board.is_check():
                raise ChessGameError("Illegal move: You must address the check first")
            if board.piece_at(move.from_square) is None:
                raise ChessGameError("No piece at starting square")
            if board.piece_at(move.from_square).color != board.turn:
                raise ChessGameError("That's not your piece")
            raise ChessGameError("Move is not legal in current position")
        
        return move

    except ValueError:
        raise ChessGameError("Invalid move format. Use UCI notation (like e2e4 or e7e8q)")

def evaluate_position(board):
    """Evaluate position based on material and checkmate only"""
    if board.is_checkmate():
        return -20000 if board.turn else 20000
    
    if board.is_stalemate():
        return 0
    
    score = 0
    # Only consider material difference/captures
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = PIECE_VALUES[piece.piece_type]
            score += value if piece.color else -value
    
    return score

def minimax(board, depth, alpha, beta, is_maximizing):
    """Enhanced minimax (with alpha-beta pruning and move ordering for a lil kick)"""
    if depth == 0 or board.is_game_over():
        return evaluate_position(board), None
        
    # Use move ordering for better pruning
    legal_moves = order_moves(board, list(board.legal_moves))
    
    if is_maximizing:
        best_score = float('-inf')
        best_move = None
        for move in legal_moves:
            board.push(move)
            score, _ = minimax(board, depth-1, alpha, beta, False)
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        best_move = None
        for move in legal_moves:
            board.push(move)
            score, _ = minimax(board, depth-1, alpha, beta, True)
            board.pop()
            
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score, best_move

def get_bot_move(board, use_minimax=True, depth=2):
    """
    Get bot move using minimax algorithm or fallback to random/capture.
    
    Args:
        board: Current chess board
        use_minimax: Whether to use minimax (True) or old random bot (False)
        depth: Search depth for minimax
    """
    try:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ChessGameError("No legal moves available - game is over")
        
        if use_minimax:
            print(f"Bot thinking (depth {depth})...")
            computer_color = board.turn
            score, move = minimax(board, depth, float('-inf'), float('inf'), True)
            
            if move is None:
                # Fallback to random move if minimax fails
                print("Minimax returned no move, using random selection")
                move = random.choice(legal_moves)
            else:
                print(f"Bot evaluation score: {score}")
            
            return move
        else:
            # Old behavior/prefer captures, otherwise random
            capture_moves = [move for move in legal_moves if board.is_capture(move)]
            
            if capture_moves:
                print(f"Bot found {len(capture_moves)} capture moves, randomly chose one")
                return random.choice(capture_moves)
            else:
                print(f"Bot found no captures, randomly chose from {len(legal_moves)} legal moves")
                return random.choice(legal_moves)
            
    except IndexError:
        raise ChessGameError("Failed to select a valid move")
    except ChessGameError:
        raise
    except Exception as e:
        raise ChessGameError(f"Error selecting bot move: {str(e)}")

def main():
    try:
        print_header()
        computer_color = get_computer_color()
        
        # Ask/prompts to see if user wants to use minimax
        use_minimax_input = input("Use minimax? (y/n, default=y): ").strip().lower()
        use_minimax = use_minimax_input != 'n'
        
        depth = 2
        if use_minimax:
            depth_input = input("Search depth? (1-4, default=2): ").strip()
            if depth_input.isdigit():
                depth = max(1, min(4, int(depth_input)))
            print(f"Using minimax with depth {depth}")
        else:
            print("Using random/capture bot")
        
        board = chess.Board()
        
        while not board.is_game_over():
            print("\nCurrent position:")
            print(board)
            
            # Bot's turn
            if (board.turn == chess.WHITE and computer_color == 'w') or \
               (board.turn == chess.BLACK and computer_color == 'b'):
                try:
                    move = get_bot_move(board, use_minimax, depth)
                    print(f"Bot (as {'white' if board.turn == chess.WHITE else 'black'}): {move.uci()}")
                    board.push(move)
                    print(f"New FEN position: {board.fen()}")
                except ChessGameError as e:
                    print(f"Bot error: {str(e)}")
                    raise
            # Player's turn
            else:
                print(f"{'White' if board.turn == chess.WHITE else 'Black'}: ", end='')
                move = get_player_move(board)
                if move is None:
                    print("Game terminated by user.")
                    return
                board.push(move)
                print(f"New FEN position: {board.fen()}")
        
        print("\nGame Over:", board.result())
        
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
