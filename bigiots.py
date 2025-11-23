#!/usr/bin/env python3
import curses
import random
import locale

locale.setlocale(locale.LC_ALL, '')

X_SIZE = 40
Y_SIZE = 23
CRASH = "Ｘ"
SPACE = "　"

DIRECTION_MAP = {
    '7': (-1, -1), '8': (0, -1), '9': (1, -1),
    'u': (-1, 0), '4': (-1, 0), 'i': (0, 0), '5': (0, 0), 'o': (1, 0), '6': (1, 0),
    'j': (-1, 1), 'k': (0, 1), 'l': (1, 1), '1': (-1, 1), '2': (0, 1), '3': (1, 1)
}

def putchara(stdscr, x, y, char):
    stdscr.addstr(int(y), int(x * 2), char)

class Rock:
    def __init__(self, max_count=120, char="＃"):
        self.max_count = max_count
        self.char = char
        self.positions = []

    def place_random(self, stdscr):
        self.positions.clear()
        for _ in range(self.max_count):
            x = random.randint(0, X_SIZE-1)
            y = random.randint(0, Y_SIZE-1)
            self.positions.append((x, y))
            putchara(stdscr, x, y, self.char)

class Enemy:
    def __init__(self, max_count=12, char="Ｏ"):
        self.max_count = max_count
        self.char = char
        self.positions = []

    def place_random(self, stdscr, rocks):
        self.positions.clear()
        while len(self.positions) < self.max_count:
            x = random.randint(0, X_SIZE-1)
            y = random.randint(0, Y_SIZE-1)
            if (x, y) not in rocks.positions:
                self.positions.append((x, y))
                putchara(stdscr, x, y, self.char)

    def move(self, stdscr, player, rocks, game):
        new_positions = []
        rocks_to_remove = []
        for idx, (x, y) in enumerate(self.positions):
            dx = 1 if x < player.x else -1 if x > player.x else 0
            dy = 1 if y < player.y else -1 if y > player.y else 0
            nx, ny = x + dx, y + dy

            # 元の位置を消す
            putchara(stdscr, x, y, SPACE)

            # プレイヤー衝突チェック
            if (nx, ny) == (player.x, player.y):
                game.gamestat = 1
                return  # すぐに終了

            # 岩との衝突判定（赤演出）
            if (nx, ny) in rocks.positions:
                stdscr.addstr(ny, nx*2, "Ｘ", curses.color_pair(1))
                stdscr.refresh()
                curses.napms(100)  # 100ms 待つ
                putchara(stdscr, nx, ny, SPACE)
                rocks_to_remove.append((nx, ny))
                continue

            # 敵同士の衝突判定
            if (nx, ny) in new_positions:
                putchara(stdscr, nx, ny, SPACE)
                new_positions = [pos for pos in new_positions if pos != (nx, ny)]
                continue

            new_positions.append((nx, ny))
            putchara(stdscr, nx, ny, self.char)

        # 岩を安全に削除
        for pos in rocks_to_remove:
            if pos in rocks.positions:
                rocks.positions.remove(pos)

        self.positions = new_positions

class Player:
    def __init__(self, char="＠"):
        self.char = char
        self.x = X_SIZE // 2
        self.y = Y_SIZE // 2

    def move(self, stdscr, key):
        if key not in DIRECTION_MAP:
            return
        dx, dy = DIRECTION_MAP[key]
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < X_SIZE and 0 <= ny < Y_SIZE:
            putchara(stdscr, self.x, self.y, SPACE)
            self.x, self.y = nx, ny
            putchara(stdscr, self.x, self.y, self.char)

class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.player = Player()
        self.rocks = Rock()
        self.enemies = Enemy()
        self.gamestat = 0

        # 色ペア初期化（赤文字）
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

    def instruction(self):
        self.stdscr.clear()
        lines = [
            "Bigiots Ver 1.0",
            "I created a word bigiot. bigiot means bigot and idiot.",
            "",
            "Mission : kill all bigiots to survive!",
            "Ｏ -- bigiots, chase player step by step.",
            "＃ -- Rock, die bigiots and player when touched. ",
            "＠ -- Player, control for bigiots to crash to rock and survive!",
            "",
            "#Key control:    　    Tenkey:",
            "#７  ８  ９            ７　８  ９",
            "#　↖ ↑  ↗　　　　　　　　↖ ↑  ↗",
            "#Ｕ← Ｉ→ Ｏ　　　　　　４← ５→ ６",
            "#　↙ ↓  ↘                ↙ ↓  ↘",
            "#Ｊ  Ｋ  Ｌ　　　　　　１  ２  ３",
            "",
            " 'i' and '5' move bigiots and don't move player",
            "             Good Luck",
            "hit key"
        ]
        start_y = max((Y_SIZE - len(lines)) // 2, 0)
        for i, line in enumerate(lines):
            if len(line)>=1 and line[0]=='#':
                start_x=20
                line=line[1:]
            else:
                start_x = max((X_SIZE*2 - len(line)) // 2, 0)
            self.stdscr.addstr(start_y + i, start_x, line)
        self.stdscr.getch()

    def init_game(self):
        self.stdscr.clear()
        self.gamestat = 0
        self.rocks.place_random(self.stdscr)
        self.enemies.place_random(self.stdscr, self.rocks)
        putchara(self.stdscr, self.player.x, self.player.y, self.player.char)

    def main_loop(self):
        while self.gamestat == 0:
            self.stdscr.refresh()
            key = self.stdscr.getkey()
            self.player.move(self.stdscr, key)
            self.check_crash()
            if self.gamestat != 0:
                break
            self.enemies.move(self.stdscr, self.player, self.rocks, self)
            self.check_crash()
            if self.gamestat != 0:
                break
            if not self.enemies.positions:
                self.gamestat = 3

    def check_crash(self):
        if (self.player.x, self.player.y) in self.enemies.positions or \
           (self.player.x, self.player.y) in self.rocks.positions:
            self.gamestat = 1

    def play(self):
        while True:
            self.instruction()
            self.init_game()
            self.main_loop()

            if self.gamestat == 1:
                putchara(self.stdscr, self.player.x, self.player.y, CRASH)
                self.stdscr.addstr(0, 0, "You Lose ")
            elif self.gamestat == 3:
                self.stdscr.addstr(0, 0, "You Win! ")

            self.stdscr.refresh()
            self.stdscr.addstr(1, 0, "Try Again? [y/n]")
            while True:
                ch = self.stdscr.getkey()
                if ch == 'n':
                    return
                if ch == 'y':
                    break

def main(stdscr):
    curses.noecho()
    curses.curs_set(0)
    game = Game(stdscr)
    game.play()

curses.wrapper(main)

