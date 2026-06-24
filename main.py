import cv2
import time
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)

detector = HandDetector(detectionCon=0.8, maxHands=1)

board = [['', '', ''], ['', '', ''], ['', '', '']]

finger_pressed = False
winner = None
game_over = False
ai_pending_time = None   # when set, AI moves after a short delay


def check_winner(b):
    for row in b:
        if row[0] != '' and row[0] == row[1] == row[2]:
            return row[0]
    for col in range(3):
        if b[0][col] != '' and b[0][col] == b[1][col] == b[2][col]:
            return b[0][col]
    if b[0][0] != '' and b[0][0] == b[1][1] == b[2][2]:
        return b[0][0]
    if b[0][2] != '' and b[0][2] == b[1][1] == b[2][0]:
        return b[0][2]
    return None


def check_draw(b):
    return all(cell != '' for row in b for cell in row)


def minimax(b, depth, is_maximizing):
    result = check_winner(b)
    if result == 'O': return 10 - depth
    if result == 'X': return depth - 10
    if check_draw(b): return 0

    if is_maximizing:
        best = -1000
        for r in range(3):
            for c in range(3):
                if b[r][c] == '':
                    b[r][c] = 'O'
                    best = max(best, minimax(b, depth + 1, False))
                    b[r][c] = ''
        return best
    else:
        best = 1000
        for r in range(3):
            for c in range(3):
                if b[r][c] == '':
                    b[r][c] = 'X'
                    best = min(best, minimax(b, depth + 1, True))
                    b[r][c] = ''
        return best


def ai_move():
    best_score, best_move = -1000, None
    for r in range(3):
        for c in range(3):
            if board[r][c] == '':
                board[r][c] = 'O'
                score = minimax(board, 0, False)
                board[r][c] = ''
                if score > best_score:
                    best_score, best_move = score, (r, c)
    if best_move:
        board[best_move[0]][best_move[1]] = 'O'


def reset():
    global board, winner, game_over, finger_pressed
    board = [['', '', ''], ['', '', ''], ['', '', '']]
    winner = None
    game_over = False
    finger_pressed = False


# Button area (below the board: y1=40, cell=150, so board ends at 40+450=490)
BTN_X, BTN_Y, BTN_W, BTN_H = 170, 475, 300, 55

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img)

    x1, y1, cell = 100, 10, 150

    # Draw board grid
    for row in range(3):
        for col in range(3):
            sx, sy = x1 + col * cell, y1 + row * cell
            cv2.rectangle(img, (sx, sy), (sx + cell, sy + cell), (255, 0, 0), 3)

    # Draw X / O
    for row in range(3):
        for col in range(3):
            val = board[row][col]
            if val:
                px = x1 + col * cell + 45
                py = y1 + row * cell + 95
                color = (0, 0, 255) if val == 'X' else (0, 255, 255)
                cv2.putText(img, val, (px, py), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 4)

    # ── Game play (only when game is active) ──────────────────────────────────
    if hands and not game_over and ai_pending_time is None:
        hand = hands[0]
        lmList = hand["lmList"]
        x, y, _ = lmList[8]

        cv2.circle(img, (x, y), 15, (0, 255, 0), cv2.FILLED)

        p1, p2 = lmList[8][:2], lmList[12][:2]
        length, _, img = detector.findDistance(p1, p2, img)

        if x1 <= x <= x1 + 3 * cell and y1 <= y <= y1 + 3 * cell:
            col_idx = int((x - x1) // cell)
            row_idx = int((y - y1) // cell)

            bx, by = x1 + col_idx * cell, y1 + row_idx * cell
            cv2.rectangle(img, (bx, by), (bx + cell, by + cell), (0, 255, 0), 5)
            cv2.putText(img, f"Box ({row_idx},{col_idx})", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if length < 35:
                if not finger_pressed:
                    if board[row_idx][col_idx] == '':
                        board[row_idx][col_idx] = 'X'
                        winner = check_winner(board)
                        if winner is None and not check_draw(board):
                            ai_pending_time = time.time() + 1.3   # 1.3s delay
                        elif winner is not None or check_draw(board):
                            game_over = True
                            finger_pressed = False
                            continue
                finger_pressed = True
            else:
                finger_pressed = False

    # ── AI delayed move ───────────────────────────────────────────────────────
    if ai_pending_time is not None and time.time() >= ai_pending_time:
        ai_pending_time = None
        ai_move()
        winner = check_winner(board)
        if winner is not None or check_draw(board):
            game_over = True
            finger_pressed = False

    # ── Winner / Draw message ─────────────────────────────────────────────────
    if winner == 'X':
        cv2.putText(img, "YOU WIN!", (180, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)
    elif winner == 'O':
        cv2.putText(img, "AI WINS!", (180, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
    elif game_over:
        cv2.putText(img, "DRAW!", (220, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 4)

    # ── Play Again button ─────────────────────────────────────────────────────
    if game_over:
        hovering = False
        if hands:
            hx, hy, _ = hands[0]["lmList"][8]
            if BTN_X <= hx <= BTN_X + BTN_W and BTN_Y <= hy <= BTN_Y + BTN_H:
                hovering = True

        btn_color = (0, 200, 0) if hovering else (40, 40, 40)
        txt_color = (0, 0, 0)   if hovering else (255, 255, 255)
        cv2.rectangle(img, (BTN_X, BTN_Y), (BTN_X + BTN_W, BTN_Y + BTN_H), btn_color, -1)
        cv2.rectangle(img, (BTN_X, BTN_Y), (BTN_X + BTN_W, BTN_Y + BTN_H), (255, 255, 255), 2)
        cv2.putText(img, "PLAY AGAIN", (BTN_X + 28, BTN_Y + 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, txt_color, 2)

        if hovering:
            p1 = hands[0]["lmList"][8][:2]
            p2 = hands[0]["lmList"][12][:2]
            length, _, img = detector.findDistance(p1, p2, img)
            if length < 35 and not finger_pressed:
                reset()
            elif length >= 35:
                finger_pressed = False   # allow re-pinch after releasing

    # ── Hint ──────────────────────────────────────────────────────────────────
    cv2.putText(img, "Pinch to place / Press R to restart  |  Q to quit",
                (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    cv2.imshow("Hand Gesture Tic Tac Toe (Minimax AI)", img)

    key = cv2.waitKey(1)
    if key == ord('r'):
        reset()
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()