import cv2
import random
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)

detector = HandDetector(
    detectionCon=0.8,
    maxHands=1
)

board = [
    ['', '', ''],
    ['', '', ''],
    ['', '', '']
]

finger_pressed = False
winner = None
game_over = False


def check_winner(board):

    # Rows
    for row in board:
        if row[0] != '' and row[0] == row[1] == row[2]:
            return row[0]

    # Columns
    for col in range(3):
        if (
            board[0][col] != '' and
            board[0][col] == board[1][col] == board[2][col]
        ):
            return board[0][col]

    # Diagonals
    if (
        board[0][0] != '' and
        board[0][0] == board[1][1] == board[2][2]
    ):
        return board[0][0]

    if (
        board[0][2] != '' and
        board[0][2] == board[1][1] == board[2][0]
    ):
        return board[0][2]

    return None


def check_draw(board):
    for row in board:
        for cell in row:
            if cell == '':
                return False
    return True


def ai_move():

    empty = []

    for r in range(3):
        for c in range(3):
            if board[r][c] == '':
                empty.append((r, c))

    if empty:
        r, c = random.choice(empty)
        board[r][c] = 'O'


while True:

    success, img = cap.read()

    if not success:
        break

    img = cv2.flip(img, 1)

    hands, img = detector.findHands(img)

    x1, y1 = 100, 100
    cell = 150

    # Draw Board
    for row in range(3):
        for col in range(3):

            start_x = x1 + col * cell
            start_y = y1 + row * cell

            cv2.rectangle(
                img,
                (start_x, start_y),
                (start_x + cell, start_y + cell),
                (255, 0, 0),
                3
            )

    # Draw X and O
    for row in range(3):
        for col in range(3):

            value = board[row][col]

            if value != '':

                pos_x = x1 + col * cell + 45
                pos_y = y1 + row * cell + 95

                color = (0, 0, 255)

                if value == 'O':
                    color = (0, 255, 255)

                cv2.putText(
                    img,
                    value,
                    (pos_x, pos_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    color,
                    4
                )

    if hands and not game_over:

        hand = hands[0]
        lmList = hand["lmList"]

        x, y, z = lmList[8]

        cv2.circle(
            img,
            (x, y),
            15,
            (0, 255, 0),
            cv2.FILLED
        )

        p1 = lmList[8][:2]
        p2 = lmList[12][:2]

        length, info, img = detector.findDistance(
            p1,
            p2,
            img
        )

        if (
            x1 <= x <= x1 + 3 * cell and
            y1 <= y <= y1 + 3 * cell
        ):

            col = int((x - x1) // cell)
            row = int((y - y1) // cell)

            box_x = x1 + col * cell
            box_y = y1 + row * cell

            cv2.rectangle(
                img,
                (box_x, box_y),
                (box_x + cell, box_y + cell),
                (0, 255, 0),
                5
            )

            cv2.putText(
                img,
                f"Box ({row},{col})",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            if length < 35:

                if not finger_pressed:

                    if board[row][col] == '':

                        board[row][col] = 'X'

                        winner = check_winner(board)

                        if winner is None and not check_draw(board):
                            ai_move()

                        winner = check_winner(board)

                        if winner is not None:
                            game_over = True

                        elif check_draw(board):
                            game_over = True

                    finger_pressed = True

            else:
                finger_pressed = False

    # Winner Messages
    if winner == 'X':

        cv2.putText(
            img,
            "YOU WIN!",
            (180, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 0),
            4
        )

    elif winner == 'O':

        cv2.putText(
            img,
            "AI WINS!",
            (180, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 255),
            4
        )

    elif game_over:

        cv2.putText(
            img,
            "DRAW!",
            (220, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 255),
            4
        )

    cv2.putText(
        img,
        "Press R to Restart",
        (20, 520),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "Hand Gesture Tic Tac Toe",
        img
    )

    key = cv2.waitKey(1)

    if key == ord('r'):

        board = [
            ['', '', ''],
            ['', '', ''],
            ['', '', '']
        ]

        winner = None
        game_over = False
        finger_pressed = False

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()