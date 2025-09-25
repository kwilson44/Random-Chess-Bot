import chess
from datetime import datetime
import random
import sys

#1. I added a custom exception class to provide clearer/testable error types
class ChessGameError(Exception):
    """Custom exception for chess game errors"""
    pass


def print_header():
    print("=====================================================")
    print("             CS 290 Chess Bot Version 0.1")
    print("=====================================================")
    print(f"Time: {datetime.now()}")

#2. I changed it a bit so get_player_move now has interactive helper commands (help, legal, fen)
#   because that improves UX and helped with debugging (without breaking the tester code)
def get_player_move(board):
    while True:
        try:
            user_move = input("Your move (or 'quit' to end, 'help' for commands): ").strip().lower()
            
            # Handle special commands
            if user_move == "quit":
                return None
            if user_move == "help":
                print("\nCommands:")
                print("- Enter moves in UCI format (like e2e4)")
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
                
            # Validate and return move
            move = validate_move(board, user_move)
            return move
            
        except ChessGameError as e:
            #3.I just added user-facing + specific error messages instead of the generic ones
            print(f"Error: {str(e)}")
        except KeyboardInterrupt:
            #4. I kept wanting to quit so I added the option to do Ctrl+C
            print("\nGame interrupted by user.")
            sys.exit(0)
        except Exception as e:
            #5. I added a catch-all to avoid crash/spot unexpected issues
            print(f"Unexpected error: {str(e)}")

#6. I just threw in a helper to get/validate computer color input (w/b) (Its good for testing/clarity)
def get_computer_color():
    while True:
        color = input("Computer Player? (w=white/b=black): ").strip().lower()
        if color in ('w', 'b'):
            return color
        print("Invalid input. Enter 'w' for white or 'b' for black")

#7. I changed validate_fen to perform basic structural checks and then uses python-chess to confirm validity
#  (Just to like catch obvious formatting problems early and return a Board for tests)
def validate_fen(fen):
    if not fen:
        return None
        
    try:
        # Check basic FEN structure
        parts = fen.split()
        if len(parts) != 6:
            raise ChessGameError("FEN must have 6 space-separated fields")
            
        # Validate piece placement
        rows = parts[0].split('/')
        if len(rows) != 8:
            raise ChessGameError("FEN must have 8 ranks separated by '/'")
            
        # Try to create a board with the FEN to validate it
        try:
            board = chess.Board(fen)
            return board
        except ValueError as e:
            #8. I swapped the ValueError for bad FENs to the ChessGameError from the library
            raise ChessGameError(f"Invalid FEN format: {str(e)}")
            
    except Exception as e:
        #9. Same #8 reasoning
        raise ChessGameError(f"Invalid FEN: {str(e)}")

#10. I tweaked the validate_move so its more central with the move-format and legality checks and has detailed messages
def validate_move(board, move_str):
    """Validates a move with detailed error checking"""
    try:
        # Check for common input mistakes
        if len(move_str) != 4:
            raise ChessGameError("Move must be exactly 4 characters (like e2e4)")
            
        if not all(c in 'abcdefgh12345678' for c in move_str):
            raise ChessGameError("Invalid characters in move. Use algebraic notation (a-h, 1-8)")
            
        # Convert to chess.Move object
        move = chess.Move.from_uci(move_str)
        
        # Check if move is legal
        if move not in board.legal_moves:
            # Get more specific about why the move is illegal
            if board.is_check():
                raise ChessGameError("Illegal move: You must address the check first")
            if board.piece_at(move.from_square) is None:
                raise ChessGameError("No piece at starting square")
            if board.piece_at(move.from_square).color != board.turn:
                raise ChessGameError("That's not your piece")
            raise ChessGameError("Move is not legal in current position")
            
        return move
        
    except ValueError:
        #11. It's a more explicit error for parse problems
        raise ChessGameError("Invalid move format. Use UCI notation (like e2e4)")

#12. Changed: I made get_bot_move its own function that:
#    - If captures exist, pick randomly from captures
#    - Otherwise pick randomly from all legal moves
#    - Raises ChessGameError with exact message when no legal moves (testable)
def get_bot_move(board):
    """Get bot move following assignment requirements"""
    try:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            #13. The test file expects this exact message... computers are fickle
            raise ChessGameError("No legal moves available - game is over")
            
        # Find all capture moves
        capture_moves = [move for move in legal_moves if board.is_capture(move)]
        
        if capture_moves:
            print(f"Bot found {len(capture_moves)} capture moves, randomly chose one")
            return random.choice(capture_moves)
        else:
            print(f"Bot found no captures, randomly chose from {len(legal_moves)} legal moves")
            return random.choice(legal_moves)
            
    except IndexError:
        #14. More error stuff catch for unexpected empty selection issues
        raise ChessGameError("Failed to select a valid move")
    except ChessGameError:
        #15. More error stuff - just re-raise known chess errors
        raise
    except Exception as e:
        #16. More error stuff again - catch-all for unexpected issues
        raise ChessGameError(f"Error selecting bot move: {str(e)}")

#17. I changed main() to be more modular/test-friendly:
#    - uses validate_fen, get_computer_color, get_bot_move, validate_move
#    - prints board before/after moves (user requested)
#    - handles KeyboardInterrupt gracefully
def main():
    try:
        print_header()
        computer_color = get_computer_color()
        
        # FEN handling with validation
        fen_input = input("Starting FEN position? (hit ENTER for standard starting position): ")
        try:
            board = validate_fen(fen_input) if fen_input else chess.Board()
        except ChessGameError as e:
            #18. Even more error stuff ahhhhhhhhhhhhhhhh
            print(f"FEN Error: {str(e)}")
            print("Using standard starting position instead.")
            board = chess.Board()
            
        while not board.is_game_over():
            # Print current board state at start of turn
            print("\nCurrent position:")
            print(board)
            
            # Bot's turn
            if (board.turn == chess.WHITE and computer_color == 'w') or \
               (board.turn == chess.BLACK and computer_color == 'b'):
                try:
                    move = get_bot_move(board)
                    print(f"Bot (as {'white' if board.turn == chess.WHITE else 'black'}): {move.uci()}")
                    board.push(move)
                    print(f"New FEN position: {board.fen()}")
                except ChessGameError as e:
                    #19. This logs bot errors then re-raise to stop execution in catastrophic cases that probably won't happen
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
            
            # Print board after move (user requested persistent ASCII board update)
            print("\nPosition after move:")
            print(board)
        
        # game over handling
        print("\nGame Over:", board.result())
        
    except KeyboardInterrupt:
        #20. exit with Ctrl+C
        print("\nGame interrupted by user.")
        sys.exit(0)
    except Exception as e:
        #21. Added fatal error logging and non-zero exit
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()