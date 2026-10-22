"""
КАК ПРАВИЛЬНО ИСПОЛЬЗОВАТЬ ШАХМАТНЫЙ ДВИЖОК:
1) ВВОД uci, РЕГИСТР ВАЖЕН!
2) ВВОД isready, РЕГИСТР ВАЖЕН!
3) ВВОД position startpos ИЛИ position startpos moves (ХОДЫ), РЕГИСТР ВАЖЕН!
4) ВВОД go ИЛИ go movetime N (КОЛИЧЕСТВО МС), РЕГИСТР ВАЖЕН!
"""




import sys
import time
import chess
import chess.polyglot

INF = 10**9
MATE = 10**6
MATE_THRESHOLD = MATE - 1000

PIECE_VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

PAWN_PST = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0,
]

KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_PST = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_PST = [
    0, 0, 5, 10, 10, 5, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]

QUEEN_PST = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -10, 5, 5, 5, 5, 5, 0, -10,
    0, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]

KING_MID_PST = [
    20, 30, 10, 0, 0, 10, 30, 20,
    20, 20, 0, 0, 0, 0, 20, 20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
]

KING_END_PST = [
    -50, -30, -30, -30, -30, -30, -30, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30,-10, 30, 40, 40, 30, -10, -30,
    -30,-10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]

PST = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
    chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST,
    chess.QUEEN: QUEEN_PST,
}

def mirror(idx):
    return chess.square_mirror(idx)

FILE_MASKS = [chess.BB_FILES[f] for f in range(8)]

ADJACENT_FILES = []
for f in range(8):
    m = 0
    if f > 0:
        m |= chess.BB_FILES[f - 1]
    if f < 7:
        m |= chess.BB_FILES[f + 1]
    ADJACENT_FILES.append(m)
    
def evaluate(board):
    if board.is_checkmate():
        return -MATE
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    mg = 0
    eg = 0
    phase = 0
    
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    
    white_mobility = 0
    black_mobility = 0
    
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        
        v = PIECE_VALUE[piece.piece_type]
        idx = sq if piece.color == chess.WHITE else mirror(sq)
        sign = 1 if piece.color == chess.WHITE else -1
        
        if piece.piece_type == chess.KING:
            mg += sign * KING_MID_PST[idx]
            eg += sign * KING_END_PST[idx]
        else:
            mg += sign * (v + PST[piece.piece_type][idx])
            eg += sign * v
            
        if piece.piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
            attacks = len(board.attacks(sq))
            if piece.color == chess.WHITE:
                white_mobility += attacks
            else:
                black_mobility += attacks
                
        if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            phase += 1
        elif piece.piece_type == chess.ROOK:
            phase += 2
        elif piece.piece_type == chess.QUEEN:
            phase += 4
            
    mg += (white_mobility - black_mobility) * 2
    
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        mg += 30
        eg += 50
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        mg -= 30
        eg -= 50
        
    for color, pawns, sign in (
        (chess.WHITE, white_pawns, 1),
        (chess.BLACK, black_pawns, -1),
    ):
        for f in range(8):
            cnt = bin(pawns & chess.BB_FILES[f]).count("1")
            if cnt > 1:
                mg -= sign * 15 * (cnt - 1)
                eg -= sign * 25 * (cnt - 1)
                
        for f in range(8):
            if pawns & chess.BB_FILES[f]:
                if not (pawns & ADJACENT_FILES[f]):
                    mg -= sign * 20
                    eg -= sign * 25
                    
        for sq in chess.SQUARES:
            if not (pawns & chess.BB_SQUARES[sq]):
                continue
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            
            enemy_pawns = black_pawns if color == chess.WHITE else white_pawns
            
            ahead_mask = 0
            if color == chess.WHITE:
                for rr in range(r + 1, 8):
                    ahead_mask |= chess.BB_RANKS[rr]
            else:
                for rr in range(0, r):
                    ahead_mask |= chess.BB_RANKS[rr]
                    
            front_files = FILE_MASKS[f] | ADJACENT_FILES[f]
            
            if not (enemy_pawns & ahead_mask & front_files):
                bonus = 20 + (r if color == chess.WHITE else 7 - r) * 15
                eg += sign * bonus
                mg += sign * bonus // 3
                
    phase = min(phase, 24)
    score = (mg * phase + eg * (24 - phase)) // 24
    return score if board.turn == chess.WHITE else -score

EXACT, LOWER, UPPER = 0, 1, 2

class TTEntry:
    __slots__ = ("depth", "value", "flag", "move")
    
    def __init__(self, depth, value, flag, move):
        self.depth = depth
        self.value = value
        self.flag = flag
        self.move = move
        
TT = {}
TT_MAX = 1_000_000
TT_HITS = 0

KILLERS = [[None, None] for _ in range(64)]
HISTORY = {}
COUNTERMOVE = {}

def score_move(board, move, tt_move, ply, prev_move):
    if move == tt_move:
        return 10**7
    
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        vv = PIECE_VALUE[victim.piece_type] if victim else 100
        av = PIECE_VALUE[attacker.piece_type] if attacker else 0
        return 10**6 + vv * 10 - av
    
    if move.promotion:
        return 10**6 + PIECE_VALUE[move.promotion]
    
    if prev_move is not None:
        cm = COUNTERMOVE.get((prev_move.from_square, prev_move.to_square))
        if cm == move:
            return 10**5 + 500
        
    if move in KILLERS[ply]:
        return 10**5
    
    return HISTORY.get((move.from_square, move.to_square), 0)

def order_moves(board, moves, tt_move, ply, prev_move):
    return sorted(
        moves,
        key=lambda m: score_move(board, m, tt_move, ply, prev_move),
        reverse=True,
    )

def update_history(move, depth):
    key = (move.from_square, move.to_square)
    HISTORY[key] = HISTORY.get(key, 0) + depth * depth
    
def quiescence(board, alpha, beta, ply):
    stand = evaluate(board)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
        
    moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
    moves = order_moves(board, moves, None, ply, None)
    
    for move in moves:
        victim = board.piece_at(move.to_square)
        if victim and stand + PIECE_VALUE[victim.piece_type] + 200 < alpha:
            continue
        
        board.push(move)
        score = -quiescence(board, -beta, -alpha, ply + 1)
        board.pop()
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
            
    return alpha

def negamax(board, depth, alpha, beta, ply, prev_move, can_null=True):
    global TT_HITS
    
    if board.is_repetition(2) or board.halfmove_clock >= 100:
        return 0
    
    if ply >= 63:
        return evaluate(board)
    
    alpha_orig = alpha
    key = chess.polyglot.zobrist_hash(board)
    entry = TT.get(key)
    tt_move = None 
    
    if entry:
        tt_move = entry.move
        if entry.depth >= depth:
            if entry.flag == EXACT:
                TT_HITS += 1
                return entry.value
            elif entry.flag == LOWER:
                alpha = max(alpha, entry.value)
            elif entry.flag == UPPER:
                beta = min(beta, entry.value)
            if alpha >= beta:
                TT_HITS += 1
                return entry.value
            
    if board.is_checkmate():
        return -MATE + ply
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    if depth <= 0:
        return quiescence(board, alpha, beta, ply)
    
    in_check = board.is_check()
    
    if not in_check and depth <= 3:
        static_eval = evaluate(board)
        if static_eval - 120 * depth >= beta:
            return static_eval
        
    if can_null and not in_check and depth >= 3 and has_non_pawn_material(board):
        board.push(chess.Move.null())
        score = -negamax(board, depth - 3, -beta, -beta + 1, ply + 1, None, False)
        board.pop()
        if score >= beta:
            return beta
        
    moves = order_moves(board, list(board.legal_moves), tt_move, ply, prev_move)
    best_value = -INF
    best_move = moves[0] if moves else None
    
    static_eval = None
    if not in_check and depth <= 2:
        static_eval = evaluate(board)
        
    for i, move in enumerate(moves):
        is_quiet = not board.is_capture(move) and not move.promotion
        
        if static_eval is not None and is_quiet and i > 0:
            if static_eval + 100 * depth + 200 < alpha:
                continue
            
        board.push(move)
        
        new_depth = depth - 1
        reduction = 0
        if depth >= 3 and i >= 3 and is_quiet and not in_check:
            reduction = 1 + (i // 6)
            if depth - reduction < 1:
                reduction = depth - 1
                
        if i == 0:
            score = -negamax(board, new_depth, -beta, -alpha, ply + 1, move)
        else:
            score = -negamax(
                board, new_depth - reduction, -alpha - 1, -alpha, ply + 1, move
            )
            if reduction > 0 and score > alpha:
                score = -negamax(
                    board, new_depth, -alpha - 1, -alpha, ply + 1, move
                )
            if alpha < score < beta:
                score = -negamax(
                    board, new_depth, -beta, -alpha, ply + 1, move
                )
                
        board.pop()
        
        if score > best_value:
            best_value = score
            best_move = move
            
        if score > alpha:
            alpha = score
            
        if alpha >= beta:
            if is_quiet:
                if move not in KILLERS[ply]:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = move
                    
                update_history(move, depth)
                
                if prev_move is not None:
                    COUNTERMOVE[
                        (prev_move.from_square, prev_move.to_square)
                    ] = move
            break
        
    flag = EXACT
    if best_value <= alpha_orig:
        flag = UPPER
    elif best_value >= beta:
        flag = LOWER
        
    if len(TT) < TT_MAX:
        old = TT.get(key)
        if old is None or depth >= old.depth or flag == EXACT:
            TT[key] = TTEntry(depth, best_value, flag, best_move)
            
    return best_value

def has_non_pawn_material(board):
    color = board.turn
    return bool(
        board.pieces(chess.KNIGHT, color)
        or board.pieces(chess.BISHOP, color)
        or board.pieces(chess.ROOK, color)
        or board.pieces(chess.QUEEN, color)
    )

def search(board, max_depth=6, time_limit=None):
    start = time.time()
    best_move = None
    best_score = 0
    prev_score = 0
    
    for depth in range(1, max_depth + 1):
        if depth <= 2:
            alpha, beta = -INF, INF
        else:
            alpha = prev_score - 50
            beta = prev_score + 50
        
        tries = 0    
        while True:
            tries += 1
            cur_best = None
            cur_score = -INF
            
            moves = order_moves(
                board, list(board.legal_moves), best_move, 0, None
            )
            
            for i, move in enumerate(moves):
                board.push(move)
                
                if i == 0:
                    score = -negamax(board, depth - 1, -beta, -alpha, 0, move)
                else:
                    score = -negamax(
                        board, depth - 1, -alpha - 1, -alpha, 0, move
                    )
                    if alpha < score < beta:
                        score = -negamax(
                            board, depth - 1, -beta, -alpha, 0, move
                        )
                        
                board.pop()
                
                if score > cur_score:
                    cur_score = score
                    cur_best = move
                if score > alpha:
                    alpha = score
                    
            if cur_score <= alpha:
                beta = (alpha + beta) // 2
                alpha = cur_score - 100
                prev_score = cur_score
                if tries > 5:
                    break
                continue
            elif cur_score >= beta:
                beta = cur_score + 100
                prev_score = cur_score
                if tries > 5:
                    break
                continue
            
            break
        
        best_move = cur_best
        best_score = cur_score
        prev_score = best_score
        
        elapsed = time.time() - start
        
        print(
            f"Глубина: {depth} | Оценка: {best_score} | "
            f"Время: {int(elapsed * 1000)} мс | Лучший ход: {best_move}",
            file=sys.stderr,
            flush=True,
        )
        
        if time_limit is not None and elapsed > time_limit:
            break
        
    return best_move, best_score

def uci_loop():
    board = chess.Board()
    
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        
        if line == "uci":
            print("id name PyEngine2000")
            print("id Artem")
            print("uciok")
            
        elif line == "isready":
            print("readyok")
            
        elif line == "ucinewgame":
            TT.clear()
            for k in HISTORY:
                HISTORY[k] = 0
            COUNTERMOVE.clear()
            board = chess.Board()
            
        elif line.startswith("position"):
            parts = line.split()
            
            if "startpos" in parts:
                board = chess.Board()
                idx = parts.index("startpos") + 1
            elif "fen" in parts:
                idx = parts.index("fen") + 1
                fen = " ".join(parts[idx:idx + 6])
                board = chess.Board(fen)
                idx += 6
            else:
                continue
            
            if idx < len(parts) and parts[idx] == "moves":
                for mv in parts[idx + 1:]:
                    board.push_uci(mv)
                    
        elif line.startswith("go"):
            parts = line.split()
            
            time_limit = None
            if "movetime" in parts:
                idx = parts.index("movetime")
                time_limit = int(parts[idx + 1]) / 1000.0
                
            print("\n" + "="*20)
            print(board)
            print("="*20 + "\n")
                
            move, score = search(
                board, max_depth=6, time_limit=time_limit
            )
            
            if move:
                san_move = board.san(move)
                piece = board.piece_at(move.from_square)
                piece_names = {
                    chess.PAWN: "Пешка",
                    chess.KNIGHT: "Конь",
                    chess.BISHOP: "Слон",
                    chess.ROOK: "Ладья",
                    chess.QUEEN: "Ферзь",
                    chess.KING: "Король",
                }
                piece_ru = piece_names[piece.piece_type]
                print(f"Лучший ход: {move.uci()} ({piece_ru} => {san_move})")
            else:
                print("Конец партии.")
            
        elif line == "quit":
            break
        
        
if __name__ == "__main__":
    uci_loop()
                    
            
                
         
        
        
        
              
                
    
    
                    
                    


                    
    
    
    
        












