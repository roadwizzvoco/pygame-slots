import pygame
import random
import os
import sys
import math
from collections import Counter

pygame.init()

WIDTH = 1000
HEIGHT = 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Slot Machine")

clock = pygame.time.Clock()

# Värvid
BLACK = (8, 8, 18)
GOLD = (255, 215, 0)
DARK_GOLD = (184, 134, 11)
LIGHT_GOLD = (255, 240, 180)
RED = (180, 20, 40)
BRIGHT_RED = (240, 60, 80)
NEON_RED = (255, 90, 110)
WHITE = (245, 245, 255)
GRAY = (60, 60, 80)
GLASS = (30, 30, 60, 140)

# Sümbolid + rewards
symbols_info = [
    {"file": "bonus.png",  "name": "BONUS",  "prob": 0.00670},
    {"file": "seitse.png", "name": "7",      "prob": 0.00446},
    {"file": "diamond.png","name": "GEM",    "prob": 0.01339},
    {"file": "cherry.png", "name": "CHERRY", "prob": 0.04464},
    {"file": "bell.png",   "name": "BELL",   "prob": 0.06920},
    {"file": "coin.png",   "name": "COIN",   "prob": 0.11161},
    {"file": "bomb.png",   "name": "BOMB",   "prob": 0.75000},
]

# Base spins for EVERY symbol shown (except BONUS – handled separately)
symbol_base_spins = {
    "7":      20,
    "GEM":    10,
    "CHERRY": 3,
    "BELL":   2,
    "COIN":   1,
    "BOMB":   0,
    "BONUS":  0,
}

SYMBOL_SIZE = 130

current_path = os.path.dirname(os.path.abspath(__file__))
for symb in symbols_info:
    try:
        img = pygame.image.load(os.path.join(current_path, symb["file"])).convert_alpha()
        symb["img"] = pygame.transform.smoothscale(img, (SYMBOL_SIZE, SYMBOL_SIZE))
    except Exception as e:
        print(f"Pilt puudu: {symb['file']} → {e}")
        symb["img"] = pygame.Surface((SYMBOL_SIZE, SYMBOL_SIZE))
        symb["img"].fill((random.randint(120,255), random.randint(80,220), random.randint(60,180)))

# Fondid
font_title  = pygame.font.SysFont("georgia", 68, bold=True)
font_big    = pygame.font.SysFont("georgia", 48, bold=True)
font_med    = pygame.font.SysFont("georgia", 34, bold=True)
font_small  = pygame.font.SysFont("arial", 22)
font_button = pygame.font.SysFont("arialblack", 46, bold=True)
font_win    = pygame.font.SysFont("impact", 72, bold=True)

# Muutujad
reels = [0, 0, 0]
spinning = [False, False, False]
spin_progress = [0.0] * 3
spin_start_time = 0
spin_durations = [0] * 3

BASE_SPIN_TIME = 550
EXTRA_DELAY_PER_REEL = 350
glow_timer = 0.0

last_win = 0
spins_left = 5           # ← CHANGED TO 5 (as you requested)

game_state = "MENU"
win_flash_timer = 0
win_flash_active = False

def draw_background():
    screen.fill(BLACK)
    for y in range(180):
        ratio = y / 180
        color = (
            int(12 + 30 * ratio),
            int(10 + 25 * ratio),
            int(28 + 40 * ratio)
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

def draw_menu():
    draw_background()
    title = font_title.render("SLOT MACHINE", True, GOLD)
    title_rect = title.get_rect(center=(WIDTH//2, 160))
    screen.blit(title, title_rect.move(6,6))
    screen.blit(title, title_rect)

    btn_rect = pygame.Rect(WIDTH//2 - 160, 380, 320, 110)
    mouse = pygame.mouse.get_pos()
    hovered = btn_rect.collidepoint(mouse)
    pressed = pygame.mouse.get_pressed()[0] and hovered

    color = BRIGHT_RED if hovered else RED
    if pressed: color = (210, 40, 80)

    pygame.draw.rect(screen, color, btn_rect, border_radius=35)
    pygame.draw.rect(screen, LIGHT_GOLD, btn_rect, width=6, border_radius=35)

    play_txt = font_button.render("PLAY", True, WHITE)
    screen.blit(play_txt, play_txt.get_rect(center=btn_rect.center))

    return btn_rect

def draw_header():
    spins_rect = pygame.Rect(WIDTH//2 - 220, 25, 440, 70)
    pygame.draw.rect(screen, (20, 18, 45), spins_rect, border_radius=18)
    pygame.draw.rect(screen, DARK_GOLD, spins_rect, width=4, border_radius=18)
    spins_txt = font_med.render(f"SPINS LEFT: {spins_left}", True, LIGHT_GOLD)
    screen.blit(spins_txt, spins_txt.get_rect(center=spins_rect.center))

def draw_paytable():
    x, y, w, h = WIDTH - 280, 120, 260, 380
    glass = pygame.Surface((w, h), pygame.SRCALPHA)
    glass.fill(GLASS)
    pygame.draw.rect(glass, (80,80,120,60), (0,0,w,h), border_radius=16)
    screen.blit(glass, (x, y))
    pygame.draw.rect(screen, DARK_GOLD, (x, y, w, h), border_radius=16, width=3)

    title = font_med.render("VÕIDUTABEL", True, GOLD)
    screen.blit(title, (x + 20, y + 15))

    y_off = y + 60
    for symb in symbols_info:
        small = pygame.transform.smoothscale(symb["img"], (48, 48))
        screen.blit(small, (x + 18, y_off + 4))

        name = font_small.render(symb["name"], True, WHITE)
        screen.blit(name, (x + 80, y_off + 8))

        base = symbol_base_spins.get(symb["name"], 0)
        if symb["name"] == "BONUS":
            desc = "+50 spins (3× only)"
            col = (255, 220, 100)
        else:
            desc = f"+{base} spins"
            col = (180, 255, 180)

        d = font_small.render(desc, True, col)
        screen.blit(d, (x + 80, y_off + 32))

        y_off += 58

def draw_slot_area():
    frame_rect = pygame.Rect(180, 140, 640, 320)
    pygame.draw.rect(screen, DARK_GOLD, frame_rect, border_radius=28, width=8)
    pygame.draw.rect(screen, GOLD, frame_rect, border_radius=28, width=3)

    inner = frame_rect.inflate(-16, -16)
    pygame.draw.rect(screen, (14, 12, 32), inner, border_radius=24)
    return inner

def draw_symbols(inner):
    global glow_timer
    start_x = inner.left + 60
    y_pos = inner.centery - SYMBOL_SIZE // 2

    for i in range(3):
        x = start_x + i * 200
        cx = x + SYMBOL_SIZE // 2
        cy = y_pos + SYMBOL_SIZE // 2

        if spinning[i]:
            p = spin_progress[i]
            offset_y = math.sin(p * math.pi * 6) * 9 * (1 - p)
            scale = 1.0 + 0.06 * math.sin(p * math.pi * 10)

            img = symbols_info[reels[i]]["img"]
            scaled = pygame.transform.smoothscale(img, (int(SYMBOL_SIZE * scale), int(SYMBOL_SIZE * scale)))
            rect = scaled.get_rect(center=(cx, cy + offset_y))

            glow_timer += 0.16
            alpha = int(80 + 70 * math.sin(glow_timer + i * 3))
            glow = pygame.Surface((SYMBOL_SIZE + 80, SYMBOL_SIZE + 80), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*NEON_RED[:3], alpha), glow.get_rect(), border_radius=30)
            screen.blit(glow, (rect.x - 40, rect.y - 40))

            screen.blit(scaled, rect.topleft)
        else:
            screen.blit(symbols_info[reels[i]]["img"], (x, y_pos))

def draw_win_effect():
    global win_flash_timer, win_flash_active
    if last_win <= 0 or not win_flash_active:
        return

    win_flash_timer += 1
    if win_flash_timer > (180 if last_win >= 20 else 120):
        win_flash_active = False
        win_flash_timer = 0
        return

    flash_alpha = int(120 + 135 * math.sin(win_flash_timer * 0.35))
    win_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if last_win >= 20:
        txt = font_win.render(f"+{int(last_win)} SPINS!", True, (255, 215, 0))
        extra = font_big.render("MEGA WIN!", True, (255, 180, 60))
        extra.set_alpha(flash_alpha)
        win_surf.blit(extra, extra.get_rect(center=(WIDTH//2, HEIGHT//2 - 130)))
    else:
        txt = font_big.render(f"+{int(last_win)} SPINS", True, (200, 255, 180))

    txt.set_alpha(flash_alpha)
    rect = txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
    win_surf.blit(txt, rect)

    screen.blit(win_surf, (0, 0))

def draw_button():
    btn_rect = pygame.Rect(WIDTH//2 - 140, 500, 280, 100)
    mouse = pygame.mouse.get_pos()
    hovered = btn_rect.collidepoint(mouse)
    pressed = pygame.mouse.get_pressed()[0] and hovered

    shadow = btn_rect.move(8 if not pressed else 4, 8 if not pressed else 4)
    pygame.draw.rect(screen, (0,0,0,180), shadow, border_radius=35)

    if spins_left <= 0:
        col = GRAY
        txt = "RESTART"
    else:
        col = NEON_RED if pressed else (BRIGHT_RED if hovered else RED)
        txt = "SPIN"

    pygame.draw.rect(screen, col, btn_rect, border_radius=35)
    pygame.draw.rect(screen, LIGHT_GOLD, btn_rect, width=5, border_radius=35)

    t = font_button.render(txt, True, WHITE)
    screen.blit(t, t.get_rect(center=btn_rect.center))

    return btn_rect

def start_spin():
    global spins_left, spinning, spin_start_time, spin_durations, spin_progress, last_win, win_flash_active

    if spins_left <= 0 or any(spinning):
        return

    last_win = 0
    win_flash_active = False

    spinning = [True] * 3
    spin_start_time = pygame.time.get_ticks()
    spin_durations = [BASE_SPIN_TIME + i * EXTRA_DELAY_PER_REEL + random.randint(-50, 50) for i in range(3)]
    spin_progress = [0.0] * 3
    spins_left -= 1

def update_reels():
    global spinning, reels, spin_progress, last_win, win_flash_active

    if not any(spinning):
        return

    elapsed = pygame.time.get_ticks() - spin_start_time
    still = False

    for i in range(3):
        if elapsed < spin_durations[i]:
            still = True
            p = elapsed / spin_durations[i]
            spin_progress[i] = p
            if random.random() < (0.78 - p * 0.68):
                reels[i] = weighted_random_symbol()
        else:
            spin_progress[i] = 1.0

    if not still:
        spinning = [False] * 3
        check_win()
        if last_win > 0:
            win_flash_active = True

def check_win():
    global spins_left, last_win, win_flash_active

    counts = Counter(reels)
    total_extra = 0
    bonus_count = 0

    for sym_idx, count in counts.items():
        sym_name = symbols_info[sym_idx]["name"]
        if sym_name == "BONUS":
            bonus_count = count
        else:
            base = symbol_base_spins.get(sym_name, 0)
            total_extra += base * count

    if bonus_count == 3:
        total_extra += 50

    if total_extra > 0:
        spins_left += total_extra
        last_win = total_extra
        win_flash_active = True

def weighted_random_symbol():
    r = random.random()
    cum = 0.0
    for i, s in enumerate(symbols_info):
        cum += s["prob"]
        if r < cum:
            return i
    return len(symbols_info) - 1

# PEA LOOP
running = True
play_rect = None
spin_rect = None

while running:
    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "MENU":
                if play_rect and play_rect.collidepoint(e.pos):
                    game_state = "GAME"
            else:
                if spin_rect and spin_rect.collidepoint(e.pos):
                    if spins_left > 0 and not any(spinning):
                        start_spin()
                    elif spins_left <= 0:
                        # Restart game
                        spins_left = 5          # ← also changed restart to 5
                        last_win = 0
                        reels = [0, 0, 0]

    draw_background()

    if game_state == "MENU":
        play_rect = draw_menu()
    else:
        draw_header()
        inner = draw_slot_area()
        draw_symbols(inner)
        draw_paytable()
        draw_win_effect()
        spin_rect = draw_button()
        update_reels()

    pygame.display.flip()

pygame.quit()
sys.exit()