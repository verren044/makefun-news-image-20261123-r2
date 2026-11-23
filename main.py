#!/usr/bin/env python3
"""news-image-20261123-r2: THE WORLD IN ONE DAY - Monday 23 November 2026.

A deterministic broadsheet front page: 13 anchor cards + 39 briefs = 52
stories, a dotted world map with numbered story dots, and a UTC day arc.
Pure Python 3.13 standard library. No network, no fonts on disk: text is
drawn with a hand-authored 5x7 bitmap font (all text uppercased at draw
time), the PNG is encoded by hand with zlib. Two runs produce
byte-identical entry.png.

Layout (1024x1024): masthead, 3 hero anchors, 5 + 5 anchor cards,
map + day arc, numbers strip, 3 columns x 13 one-line briefs, footer.
"""
import argparse
import hashlib
import os
import struct
import sys
import zlib

W, H = 1024, 1024

PAPER = (247, 242, 231)
INK = (20, 20, 20)
RED = (179, 38, 30)
BLUE = (29, 78, 137)
GOLD = (176, 132, 30)
TEAL = (15, 110, 105)
GREY = (110, 106, 96)
CARD = (255, 253, 247)
SEA = (214, 230, 238)

# ---------------------------------------------------------------- 5x7 font
# One line per glyph: CHAR=rrrrr rrrrr ... (7 rows of 5 bits, 1 = ink).
_FONT_RAW = """
A=01110 10001 10001 11111 10001 10001 10001
B=11110 10001 10001 11110 10001 10001 11110
C=01110 10001 10000 10000 10000 10001 01110
D=11110 10001 10001 10001 10001 10001 11110
E=11111 10000 10000 11110 10000 10000 11111
F=11111 10000 10000 11110 10000 10000 10000
G=01110 10001 10000 10111 10001 10001 01111
H=10001 10001 10001 11111 10001 10001 10001
I=01110 00100 00100 00100 00100 00100 01110
J=00111 00010 00010 00010 00010 10010 01100
K=10001 10010 10100 11000 10100 10010 10001
L=10000 10000 10000 10000 10000 10000 11111
M=10001 11011 10101 10101 10001 10001 10001
N=10001 11001 10101 10011 10001 10001 10001
O=01110 10001 10001 10001 10001 10001 01110
P=11110 10001 10001 11110 10000 10000 10000
Q=01110 10001 10001 10001 10101 10010 01101
R=11110 10001 10001 11110 10100 10010 10001
S=01111 10000 10000 01110 00001 00001 11110
T=11111 00100 00100 00100 00100 00100 00100
U=10001 10001 10001 10001 10001 10001 01110
V=10001 10001 10001 10001 10001 01010 00100
W=10001 10001 10001 10101 10101 11011 10001
X=10001 10001 01010 00100 01010 10001 10001
Y=10001 10001 01010 00100 00100 00100 00100
Z=11111 00001 00010 00100 01000 10000 11111
0=01110 10001 10011 10101 11001 10001 01110
1=00100 01100 00100 00100 00100 00100 01110
2=01110 10001 00001 00110 01000 10000 11111
3=11111 00010 00100 00010 00001 10001 01110
4=00010 00110 01010 10010 11111 00010 00010
5=11111 10000 11110 00001 00001 10001 01110
6=00110 01000 10000 11110 10001 10001 01110
7=11111 00001 00010 00100 01000 01000 01000
8=01110 10001 10001 01110 10001 10001 01110
9=01110 10001 10001 01111 00001 00010 01100
.=00000 00000 00000 00000 00000 01100 01100
,=00000 00000 00000 00000 01100 00100 01000
:=00000 01100 01100 00000 01100 01100 00000
;=00000 01100 01100 00000 01100 00100 01000
!=00100 00100 00100 00100 00100 00000 00100
?=01110 10001 00001 00110 00100 00000 00100
-=00000 00000 00000 01110 00000 00000 00000
'=00100 00100 01000 00000 00000 00000 00000
(=00010 00100 01000 01000 01000 00100 00010
)=01000 00100 00010 00010 00010 00100 01000
/=00001 00010 00010 00100 01000 01000 10000
%=11001 11010 00010 00100 01000 01011 10011
$=00100 01111 10100 01110 00101 11110 00100
+=00000 00100 00100 11111 00100 00100 00000
==00000 00000 11111 00000 11111 00000 00000
&=01100 10010 10100 01000 10101 10010 01101
*=00000 10101 01110 11111 01110 10101 00000
"=01010 01010 00000 00000 00000 00000 00000
"""

def _build_font():
    font = {}
    for line in _FONT_RAW.strip().splitlines():
        if line.startswith("=="):
            ch, rows = "=", line[2:]
        else:
            ch, rows = line.split("=", 1)
        font[ch] = tuple(rows.split())
    font[" "] = ("00000",) * 7
    return font

FONT = _build_font()
CHAR_W = 6  # 5 px glyph + 1 px gap, at scale 1
CHAR_H = 7


def text_w(s, scale):
    return len(s) * CHAR_W * scale - scale


def wrap(s, width, scale):
    """Greedy word wrap; returns list of lines fitting width px."""
    words = s.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(t, scale) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d <= r * r:
                    self.set(xx, yy, c)
                elif not fill and abs(d - r * r) <= r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        # Scanline fill for a simple polygon.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(xs[i], xs[i + 1] + 1):
                    self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r, row in enumerate(g):
                for col, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + col * scale, y + r * scale, scale, scale, c)
            cx += CHAR_W * scale
        return cx

    def text_c(self, cx, y, s, scale, c):
        self.text(cx - text_w(s, scale) // 2, y, s, scale, c)

    def text_r(self, x, y, s, scale, c):
        self.text(x - text_w(s, scale), y, s, scale, c)

    def para(self, x, y, s, width, scale, c, lh=None):
        lh = lh or (CHAR_H * scale + scale)
        for ln in wrap(s, width, scale):
            self.text(x, y, ln, scale, c)
            y += lh
        return y


# ---------------------------------------------------------------- world map
# Coarse equirectangular land mask, 96 cols x 44 rows, hand-drawn.
_MAP_ROWS = [
    "........................................................................................",
    "........................................................................................",
    "....##################...........#########.....##########################################..",
    "...###################...........##########....#########################################...",
    "..####################.....####...##########....##########################################..",
    "..###################......######..#########.....#########################################..",
    "...##################.......#####...########......########################################...",
    "...#################.........####....#######.......######################################....",
    "....################..........###.....######........####################################.....",
    "....###############...........###......#####.........##################################......",
    ".....##############............##.......#####.........################################........",
    ".....#############.............##........####....##....#############################...........",
    "......###########..............#.........####...####....##########################.............",
    "......##########.......................######..#####....#######################..............",
    ".......########.........................#####################..#################..............",
    "........######..........................######################...##############...............",
    "........#####...........................#######################....############................",
    ".........###............................########################.....##########.................",
    ".........##.............................#########################.....########..................",
    "........................................##########################....######...................",
    "........................................###########################....####....................",
    ".........................................##########################.....##.....................",
    ".........................................#########################..............................",
    "..........................................#######################.............................",
    "..........................................######################..............................",
    "...........................................####################...............................",
    "............................................##################..........................##....",
    ".............................................################.........................####....",
    "..............................................##############..........................######..",
    "...............................................############...........................######..",
    "................................................##########............................####...",
    ".................................................########.............................##....",
    "..................................................######....................................",
    "...................................................####.....................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
    "........................................................................................",
]

# (lon, lat) of each anchor story, for the numbered map dots.
DOTS = [
    (56, 26), (-74, 40), (30, 36), (30, 50), (-107, 25), (107, -6),
    (77, 28), (174, -41), (-74, 40), (127, 37), (-9, 38), (96, 21),
    (-115, 36),
]
# Nudges so neighbouring dots do not overlap: 3 away from 4 (Kyiv),
# 5 away from 13 (US west coast), 9 away from 2 (New York).
DOT_NUDGE = {2: (-14, 14), 4: (14, 12), 8: (-12, -10)}


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, SEA)
    cw, ch = w / 96.0, h / 44.0
    for r, row in enumerate(_MAP_ROWS):
        for col, bit in enumerate(row):
            if bit == "#":
                dx = int(x + col * cw)
                dy = int(y + r * ch)
                cv.rect(dx, dy, max(2, int(cw) - 1), max(2, int(ch) - 1), (86, 122, 92))
    # graticule
    for gx in range(1, 6):
        cv.vline(x + w * gx // 6, y, h, (255, 255, 255))
    for gy in range(1, 3):
        cv.hline(x, y + h * gy // 3, w, (255, 255, 255))
    # numbered dots
    for i, (lon, lat) in enumerate(DOTS):
        dx = int(x + (lon + 180) / 360.0 * w)
        dy = int(y + (90 - lat) / 180.0 * h)
        ox, oy = DOT_NUDGE.get(i, (0, 0))
        dx, dy = dx + ox, dy + oy
        num = str(i + 1)
        cc = TEAL if i == 8 else RED
        cv.circle(dx, dy, 9, cc)
        cv.circle(dx, dy, 9, (255, 255, 255), fill=False)
        cv.text(dx - 3 if len(num) == 1 else dx - 6, dy - 4, num, 1, (255, 255, 255))


# ---------------------------------------------------------------- pictograms
def icon(cv, x, y, kind, c):
    if kind == "ship":  # Hormuz: hull + mast + blast
        cv.poly([(x + 4, y + 26), (x + 44, y + 26), (x + 38, y + 34), (x + 10, y + 34)], c)
        cv.vline(x + 24, y + 8, 18, c, 3)
        cv.rect(x + 14, y + 16, 20, 8, c)
        for dx, dy in ((46, 6), (52, 12), (46, 18), (56, 10)):
            cv.line(x + dx - 3, y + dy, x + dx + 3, y + dy, RED)
            cv.line(x + dx, y + dy - 3, x + dx, y + dy + 3, RED)
    elif kind == "chart":  # markets: falling line
        cv.hline(x + 4, y + 34, 52, c, 2)
        cv.vline(x + 4, y + 4, 30, c, 2)
        pts = [(8, 8), (20, 16), (30, 12), (42, 28), (54, 34)]
        for a, b in zip(pts, pts[1:]):
            cv.line(x + a[0], y + a[1], x + b[0], y + b[1], RED)
        cv.line(x + 54, y + 34, x + 48, y + 34, RED)
        cv.line(x + 54, y + 34, x + 54, y + 28, RED)
    elif kind == "globe":  # climate: globe + heat bar
        cv.circle(x + 22, y + 18, 15, c, fill=False)
        cv.hline(x + 7, y + 18, 30, c)
        cv.line(x + 12, y + 6, x + 32, y + 30, c)
        cv.line(x + 32, y + 6, x + 12, y + 30, c)
        cv.rect(x + 46, y + 6, 6, 26, RED)
        cv.rect(x + 46, y + 28, 6, 4, c)
    elif kind == "drone":  # Kyiv: building + drone
        cv.rect(x + 6, y + 12, 18, 22, c)
        cv.rect(x + 28, y + 20, 14, 14, c)
        cv.circle(x + 48, y + 10, 4, RED)
        cv.hline(x + 40, y + 10, 16, c, 2)
        cv.hline(x + 40, y + 6, 16, GREY, 1)
    elif kind == "badge":  # capture: star badge
        cv.circle(x + 28, y + 18, 15, c, fill=False)
        cv.poly([(x + 28, y + 7), (x + 31, y + 14), (x + 39, y + 14),
                 (x + 33, y + 19), (x + 35, y + 27), (x + 28, y + 22),
                 (x + 21, y + 27), (x + 23, y + 19), (x + 17, y + 14),
                 (x + 25, y + 14)], RED)
    elif kind == "flame":  # factory fire
        cv.poly([(x + 28, y + 4), (x + 38, y + 18), (x + 34, y + 24),
                 (x + 40, y + 30), (x + 28, y + 36), (x + 16, y + 30),
                 (x + 22, y + 24), (x + 18, y + 18)], RED)
        cv.poly([(x + 28, y + 18), (x + 33, y + 26), (x + 28, y + 32),
                 (x + 23, y + 26)], GOLD)
    elif kind == "flags":  # Nepal-India: two flags
        cv.rect(x + 6, y + 8, 20, 12, RED)
        cv.rect(x + 30, y + 8, 20, 12, BLUE)
        cv.vline(x + 6, y + 8, 26, c, 2)
        cv.vline(x + 30, y + 8, 26, c, 2)
        cv.hline(x + 4, y + 34, 48, c, 2)
    elif kind == "bat":  # cricket: bat + ball
        cv.line(x + 14, y + 6, x + 34, y + 30, c)
        cv.rect(x + 30, y + 26, 12, 5, c)
        cv.circle(x + 46, y + 10, 5, RED)
        cv.hline(x + 6, y + 34, 44, c, 2)
    elif kind == "robot":  # lethal AI: robot head
        cv.rect(x + 16, y + 10, 24, 18, c)
        cv.vline(x + 28, y + 4, 6, c, 2)
        cv.circle(x + 28, y + 4, 2, RED)
        cv.rect(x + 20, y + 16, 4, 4, PAPER)
        cv.rect(x + 32, y + 16, 4, 4, PAPER)
        cv.hline(x + 20, y + 24, 16, PAPER, 2)
    elif kind == "cap":  # exam: mortarboard
        cv.poly([(x + 6, y + 14), (x + 28, y + 6), (x + 50, y + 14),
                 (x + 28, y + 22)], c)
        cv.rect(x + 20, y + 20, 16, 10, c)
        cv.vline(x + 50, y + 14, 10, RED, 2)
    elif kind == "crowd":  # Lisbon march
        for cx in (14, 28, 42):
            cv.circle(x + cx, y + 12, 5, c)
            cv.rect(x + cx - 6, y + 18, 12, 14, c)
        cv.hline(x + 4, y + 34, 48, RED, 2)
    elif kind == "scales":  # Myanmar / ASEAN
        cv.vline(x + 28, y + 6, 26, c, 2)
        cv.hline(x + 12, y + 8, 32, c, 2)
        cv.line(x + 12, y + 8, x + 6, y + 20, c)
        cv.line(x + 12, y + 8, x + 18, y + 20, c)
        cv.line(x + 44, y + 8, x + 38, y + 20, c)
        cv.line(x + 44, y + 8, x + 50, y + 20, c)
        cv.hline(x + 4, y + 20, 8, RED, 2)
        cv.hline(x + 36, y + 20, 8, RED, 2)
        cv.hline(x + 20, y + 32, 16, c, 2)
    elif kind == "car":  # F1: race car + flag
        cv.rect(x + 8, y + 20, 36, 8, c)
        cv.rect(x + 16, y + 12, 18, 8, c)
        cv.circle(x + 16, y + 30, 5, INK)
        cv.circle(x + 38, y + 30, 5, INK)
        cv.vline(x + 50, y + 4, 22, c, 2)
        cv.rect(x + 50, y + 4, 8, 6, RED)


# ---------------------------------------------------------------- content
# 13 anchor cards: (number, region, headline, subhead, icon, accent)
ANCHORS = [
    (1, "MIDDLE EAST", "WAR ON THE STRAIT", "Iran's missiles hit a US base in Bahrain; Houthis fire on Saudi Arabia; tankers come under fire.", "ship", RED),
    (2, "MARKETS", "NVIDIA -14%: THE AI TRADE CRACKS", "S&P 500 in correction after its worst week since 2020; Nasdaq -10%; Bitcoin under $60,000.", "chart", RED),
    (3, "CLIMATE", "COP31 COLLAPSES: NO FOSSIL-FUEL DEAL", "Turkiye's draft drops 'fossil fuels'; talks end with no deal.", "globe", TEAL),
    (4, "UKRAINE", "KYIV FLAT HIT: 14 MISSING", "Russian drone flattens a block in the Kyiv region; Ukraine sets a Russian cargo ship ablaze off Finland.", "drone", BLUE),
    (5, "MEXICO", "MOST-WANTED CARTEL BOSS SEIZED", "Troops capture 'El Chapo Isidro' after Sinaloa firefights leave 11 dead.", "badge", BLUE),
    (6, "INDONESIA", "FACTORY FIRE: 7 FOUND, 50 MISSING", "Rescuers dig through a burnt-out factory as families wait at the gates.", "flame", RED),
    (7, "SOUTH ASIA", "NEPAL PM SHAH MEETS MODI", "Two-day state visit to Delhi: talks on ties, trade and the region.", "flags", TEAL),
    (8, "SPORT", "INDIA 720/9: A RECORD ON NZ SOIL", "Rahul 136, Pant 128 as India declare in Wellington; New Zealand trail by 233.", "bat", GOLD),
    (9, "UNITED NATIONS", "UN KEEPS TALKING ON KILLER ROBOTS", "States agree to continue negotiations on lethal autonomous weapons.", "robot", BLUE),
    (10, "KOREA", "MINISTER QUITS OVER AI CHEATING", "South Korea's education chief resigns as an exam-cheating scandal spreads.", "cap", TEAL),
    (11, "EUROPE", "LISBON MARCHES AS COSTS BITE", "Thousands fill the streets over living costs; anger at prices boils over.", "crowd", GOLD),
    (12, "SE ASIA", "JUNTA CALLS ASEAN RULING UNFAIR", "Myanmar's army-backed government hits back; Malaysia turns to the UN.", "scales", BLUE),
    (13, "SPORT", "VERSTAPPEN WINS IN VEGAS AGAIN", "Third win in four years on the Strip; Hamilton penalised after a stewards' call.", "car", GOLD),
]

# 39 briefs, numbered 14-52, one line each.
BRIEFS = [
    "INDIA-PAKISTAN CRICKET HEADS TO QATAR STADIUMS",
    "HYDERABAD STUDENTS PROTEST OVER FACULTY REMARKS",
    "ICJ MYANMAR RULING: MALAYSIA TO WORK WITH UN, OIC",
    "AUSTRALIA REBUKES US BUDGET OFFICE OVER AUKUS",
    "US LAWMAKER THREATENS SPACEX STARSHIELD FUNDS",
    "SETTLER VIOLENCE IS JEWISH TERRORISM: EISENKOT",
    "BAHRAIN: 2 HURT IN SATURDAY IRANIAN STRIKES",
    "LIBYA: DRONE HITS RUSSIAN SHIP; 10 HURT",
    "RUSSIAN CARGO SHIP STILL BURNING OFF FINLAND",
    "UK TO BUILD UKRAINIAN DRONES IN NEW DEAL",
    "UKRAINE COUNTER-ATTACKS NEAR SUMY, RUSSIA RETREATS",
    "NVIDIA CHIP NETWORK TO CHINA: NEW DETAILS EMERGE",
    "SEC PROBE INTO NVIDIA DISCLOSURES, SAYS WSJ",
    "HUANG TO TESTIFY AT SENATE HEARING, AIDE SAYS",
    "ANTHROPIC IPO COOLS AFTER RECORD $83 DEBUT",
    "S&P 500 IN CORRECTION; DOW DOWN 950 FRIDAY",
    "BITCOIN ETF OUTFLOWS $582M AS FEAR INDEX HITS 9",
    "FED DECIDES 9 DEC; PCE REPORT DUE WEDNESDAY",
    "ATP FINALS: ALCARAZ FIGHTS PAST SHELTON",
    "ZVEREV BEATS MEDVEDEV; TITLE MATCH SET",
    "PAKISTAN BEAT SRI LANKA 1-0 IN TEST SERIES",
    "AUSTRALIA EDGE ENGLAND IN T20 BY 3 WICKETS",
    "FIROUZJA WINS TOTAL CHESS WORLD CHAMPIONSHIP",
    "WILL JACKS OUT OF AUSTRALIA TOUR, BROKEN HAND",
    "CHAHAL JOINS BJP; NAMED TO OBC MORCHA PANEL",
    "PATTINSON NAMED AS NEW JAMES BOND",
    "IFFI 2026 HOSTS BRICS FILM ROUNDTABLE",
    "MODI OPENS AI CENTRE AT IIT PATNA",
    "AMIT SHAH PUSHES INFRA IN ARUNACHAL",
    "TATA STEEL IN RS 28,000 CRORE APL APOLLO DEAL",
    "RAJYA SABHA MP WADKUTE DIES IN DELHI",
    "INDIA, BULGARIA TALK BILATERAL TIES, IMEC",
    "SAUDI-LED COALITION INTERCEPTS HOUTHI MISSILE",
    "SWIMMER CROSSES HORMUZ FOR IRAN'S ANIMALS",
    "WORLD CHESS TITLE MATCH OPENS WITH CEREMONY",
    "LEEDS STUN CHELSEA 4-1; CITY, ARSENAL HELD",
    "REAL MADRID BEAT CELTA 2-1 IN LA LIGA",
    "GERMANY THRASH NETHERLANDS 5-0",
    "MAN CITY HELD 1-1 BY FULHAM AT HOME",
]

DAY_ARC = [
    ("EARLY", "UN states agree to keep talking on lethal AI weapons (00:02 UTC)."),
    ("MORNING", "Nepal PM Shah begins talks with Modi in Delhi."),
    ("AFTERNOON", "COP31 draft drops 'fossil fuels'; climate talks collapse."),
    ("EVENING", "Reports land of Iran's strikes on a US base in Bahrain."),
]


# ---------------------------------------------------------------- build
def build():
    cv = Canvas(W, H, PAPER)
    mx = 14
    # --- masthead
    cv.text(mx, 12, "MAKE.FUN DAILY FRONT PAGE", 1, GREY)
    cv.text_r(W - mx, 12, "NO. 23", 1, GREY)
    cv.text(mx, 26, "THE WORLD IN ONE DAY", 6, INK)
    cv.hline(mx, 76, W - 2 * mx, INK, 3)
    cv.text(mx, 84, "MONDAY 23 NOVEMBER 2026", 2, RED)
    cv.text_r(W - mx, 84, "52 STORIES - 6 CONTINENTS - 1 DAY", 2, INK)
    cv.hline(mx, 104, W - 2 * mx, INK, 1)

    # --- hero row: anchors 1-3
    y = 112
    cw = (W - 2 * mx - 20) // 3
    ch = 168
    for i in range(3):
        n, reg, head, sub, kind, acc = ANCHORS[i]
        x = mx + i * (cw + 10)
        card(cv, x, y, cw, ch, n, reg, head, sub, kind, acc, hero=True)
    # --- band 2: anchors 4-8
    y = 288
    cw = (W - 2 * mx - 40) // 5
    ch = 158
    for i in range(4, 9):
        x = mx + (i - 4) * (cw + 10)
        card(cv, x, y, cw, ch, *ANCHORS[i], hero=False)
    # --- band 3: anchors 9-13
    y = 454
    ch = 146
    for i in range(9, 13):
        x = mx + (i - 9) * (cw + 10)
        card(cv, x, y, cw, ch, *ANCHORS[i], hero=False)

    # --- map + day arc
    y = 608
    mh = 148
    cv.text(mx, y, "WHERE IT HAPPENED", 2, INK)
    cv.text(mx + 300, y, "1-13: THE ANCHOR STORIES, PINNED", 1, GREY)
    draw_map(cv, mx, y + 20, 640, mh - 20)
    ax = mx + 660
    aw = W - mx - ax
    cv.text(ax, y, "HOW THE DAY UNFOLDED", 2, INK)
    yy = y + 24
    for slot, txt in DAY_ARC:
        cv.rect(ax, yy + 2, 8, 8, RED)
        cv.text(ax + 14, yy, slot, 1, RED)
        yy = cv.para(ax + 14, yy + 11, txt, aw - 14, 1, INK, lh=10) + 2
    # --- by-the-numbers strip
    ny = 782
    cv.hline(mx, ny, W - 2 * mx, GOLD, 2)
    cv.text_c(W // 2, ny + 6, "720/9 INDIA'S RECORD  |  -14% NVIDIA IN ONE DAY  |  $58,895 BITCOIN  |  52 STORIES", 1, INK)

    # --- briefs
    y = 806
    cv.hline(mx, y, W - 2 * mx, INK, 2)
    cv.text(mx, y + 8, "THE REST OF THE DAY", 2, INK)
    cv.text_r(W - mx, y + 8, "39 MORE STORIES", 2, RED)
    by = y + 30
    colw = (W - 2 * mx - 20) // 3
    for col in range(3):
        x = mx + col * (colw + 10)
        for r in range(13):
            n = 14 + col * 13 + r
            t = BRIEFS[n - 14]
            cv.text(x, by + r * 12, "%d." % n, 1, RED)
            cv.text(x + 24, by + r * 12, t, 1, INK)

    # --- footer
    cv.hline(mx, 1000, W - 2 * mx, INK, 1)
    cv.text(mx, 1006, "ALL STORIES AS REPORTED ON 23 NOV 2026 - TIMES UTC - DRAWN, NOT PHOTOGRAPHED", 1, GREY)
    return cv


def card(cv, x, y, w, h, n, reg, head, sub, kind, acc, hero):
    cv.rect(x, y, w, h, CARD)
    cv.rect(x, y, w, h, INK)  # border via outline trick below
    cv.rect(x + 1, y + 1, w - 2, h - 2, CARD)
    cv.rect(x, y, w, 4, acc)
    num = "%d" % n
    cv.text(x + 8, y + 10, num, 2, acc)
    cv.text(x + 8 + text_w(num, 2) + 6, y + 13, reg, 1, GREY)
    if hero:
        icon(cv, x + w - 66, y + 10, kind, acc)
        hy = y + 34
        for ln in wrap(head, w - 16, 3):
            cv.text(x + 8, hy, ln, 3, INK)
            hy += 24
        cv.para(x + 8, hy + 2, sub, w - 16, 2, INK, lh=17)
    else:
        icon(cv, x + w - 52, y + 8, kind, acc)
        hy = y + 44
        for ln in wrap(head, w - 16, 2):
            cv.text(x + 8, hy, ln, 2, INK)
            hy += 16
        cv.para(x + 8, hy + 2, sub, w - 16, 1, INK, lh=10)


# ---------------------------------------------------------------- PNG out
def png_bytes(cv):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)
    outdir = args.output or os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    # sanity: 52 stories, briefs fit one line at scale 1 in a column
    assert len(ANCHORS) == 13 and len(BRIEFS) == 39
    colw = (W - 28 - 20) // 3
    for i, b in enumerate(BRIEFS):
        assert text_w("%d. " % (14 + i) + b, 1) <= colw, "brief too long: %s" % b
    cv = build()
    data = png_bytes(cv)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("stories=%d anchors=%d briefs=%d" % (len(ANCHORS) + len(BRIEFS), len(ANCHORS), len(BRIEFS)))
    print("size=%d bytes sha256=%s" % (len(data), hashlib.sha256(data).hexdigest()))
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
