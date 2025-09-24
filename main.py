import chess
from datetime import datetime
import random

#helper functions

#prints the header before game begins
def print_header():
    print("=====================================================")
    print("             CS 290 Chess Bot Version 0.1")
    print("=====================================================")
    print(f"Time: {datetime.now()}")

def main():
    print_header()

    #get valid input for computer color
    while True: 
        computer_color = input("Computer Player? ").lower()
        if computer_color in ("w", "b"):
            break
        else:
            print("Invalid input, please enter 'w' for white or 'b' for black")

    #get starting fen (optional) or start new board
    fen = input("Starting FEN position? (hit ENTER for standard starting position): ")
    if fen:
        board = chess.Board(fen)
    else:
        board = chess.Board()
    print(board)

    #main while loop for the game
    while not board.is_game_over():
        
        #check if it's the bot's turn
        if (board.turn == chess.WHITE and computer_color == 'w') or (board.turn == chess.BLACK and computer_color == 'b'):

            #find out if bot can capture
            legal_moves = list(board.legal_moves)
            capture_moves = [i for i in legal_moves if board.is_capture(i)]
            if capture_moves:
                move = random.choice(capture_moves)
            else:
                move = random.choice(legal_moves)
            board.push(move)
            
            if chess.WHITE and computer_color == 'w':
                print(f"Bot (as white): {move.uci()}")
            else: 
                print(f"Bot (as black): {move.uci()}")

        #player move
            user_move = input("Your move: ").strip() # ADD ERROR HANDLING HERE!
            move = chess.Move.from_uci(user_move)
            try: 
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Invalid move, try again.")
                continue
            except:
                print("Invalid input")


        print(board)
        print("New FEN position", board.fen())

    print("Game Over:", board.result())

    #print messages depending on winner/looser
    outcome = board.outcome()
    if outcome.winner == chess.WHITE and computer_color == 'w':
        print("Haha. You lost to a computer.")


if __name__ == "__main__":
    main()