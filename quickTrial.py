import chess

board = chess.Board()

next_move = chess.Move.from_uci("e2e4")
board.push(next_move)
print(board)