import pygame
import random
import os
import sys
import math
from collections import Counter

pygame.init()

WIDTH = 1280
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Slot Machine")

clock = pygame.time.Clock()

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

current_path = os.path.dirname(os.path.abspath(__file__))
try:
    background_img = pygame.image.load(os.path.join(current_path, "background.png")).convert()
    background_img = pygame.transform.smoothscale(background_img, (WIDTH, HEIGHT))
except:
    background_img = None

symbols_info = [
    {"file": "bonus.png",  "name": "BONUS",  "prob": 0.00536},
    {"file": "seitse.png", "name": "7",      "prob": 0.003568},
    {"file": "diamond.png","name": "GEM",    "prob": 0.010712},
    {"file": "cherry.png", "name": "CHERRY", "prob": 0.035712},
    {"file": "bell.png",   "name": "BELL",   "prob": 0.05536},
    {"file": "coin.png",   "name": "COIN",   "prob": 0.089288},
    {"file": "bomb.png",   "name": "BOMB",   "prob": 0.80000},
]

symbol_base_spins = {
    "7":      20,
    "GEM":    10,
    "CHERRY": 3,
    "BELL":   2,
    "COIN":   1,
    "BOMB":   0,
    "BONUS":  0,
}

SYMBOL_SIZE = 160

for symb in symbols_info:
    try:
        img = pygame.image.load(os.path.join(current_path, symb["file"])).convert_alpha()
        symb["img"] = pygame.transform.smoothscale(img, (SYMBOL_SIZE, SYMBOL_SIZE))
    except:
        symb["img"] = pygame.Surface((SYMBOL_SIZE, SYMBOL_SIZE))
        symb["img"].fill((random.randint(120,255), random.randint(80,220), random.randint(60,180)))

font_title  = pygame.font.SysFont("georgia", 68, bold=True)
font_big    = pygame.font.SysFont("georgia", 48, bold=True)
font_med    = pygame.font.SysFont("georgia", 34, bold=True)
font_small  = pygame.font.SysFont("arial", 21)
font_button = pygame.font.SysFont("arialblack", 46, bold=True)
font_win    = pygame.font.SysFont("impact", 72, bold=True)

reels = [0, 0, 0]
spinning = [False, False, False]
spin_progress = [0.0] * 3
spin_start_time = 0
spin_durations = [0] * 3

BASE_SPIN_TIME = 550
EXTRA_DELAY_PER_REEL = 350

last_win = 0
spins_left = 5

game_state = "MENU"
win_flash_timer = 0
win_flash_active = False

def draw_background():
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(BLACK)

def draw_menu():
    draw_background()
    title = font_title.render("SLOT MACHINE", True, GOLD)
    title_rect = title.get_rect(center=(WIDTH//2, 160))
    screen.blit(title, title_rect.move(6,6))
    screen.blit(title, title_rect)

    btn_rect = pygame.Rect(WIDTH//2 - 180, 380, 360, 110)
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
    spins_rect = pygame.Rect(WIDTH//2 - 240, 25, 480, 70)
    pygame.draw.rect(screen, (20, 18, 45), spins_rect, border_radius=18)
    pygame.draw.rect(screen, DARK_GOLD, spins_rect, width=4, border_radius=18)
    spins_txt = font_med.render(f"SPINS LEFT: {spins_left}", True, LIGHT_GOLD)
    screen.blit(spins_txt, spins_txt.get_rect(center=spins_rect.center))

def draw_paytable():
    x = WIDTH - 225 
    y = 60
    w = 190   
    h = 630 

    glass = pygame.Surface((w, h), pygame.SRCALPHA)
    glass.fill(GLASS)
    pygame.draw.rect(glass, (80,80,120,60), (0,0,w,h), border_radius=22)
    screen.blit(glass, (x, y))
    pygame.draw.rect(screen, DARK_GOLD, (x, y, w, h), border_radius=22, width=4)

    y_off = y + 70
    icon_size = 70           

    for symb in symbols_info:
        small = pygame.transform.smoothscale(symb["img"], (icon_size, icon_size))
        screen.blit(small, (x + 18, y_off + 8))

        name = font_small.render(symb["name"], True, WHITE)
        screen.blit(name, (x + 72, y_off + 10))

        base = symbol_base_spins.get(symb["name"], 0)
        if symb["name"] == "BONUS":
            desc = "+100 spins"
            col = (255, 220, 100)
        else:
            desc = f"+{base} spins"
            col = (180, 255, 180)

        d = font_small.render(desc, True, col)
        screen.blit(d, (x + 72, y_off + 36))

        y_off += 72          

def draw_slot_area():
    frame_rect = pygame.Rect(WIDTH//2 - 410, 155, 820, 410)
    pygame.draw.rect(screen, DARK_GOLD, frame_rect, border_radius=32, width=9)
    pygame.draw.rect(screen, GOLD, frame_rect, border_radius=32, width=3)

    inner = frame_rect.inflate(-24, -24)
    pygame.draw.rect(screen, (14, 12, 32), inner, border_radius=26)
    return inner

def draw_symbols(inner):
    start_x = inner.left + 85
    y_pos = inner.centery - SYMBOL_SIZE // 2 - 8

    for i in range(3):
        x = start_x + i * 265
        cx = x + SYMBOL_SIZE // 2
        cy = y_pos + SYMBOL_SIZE // 2

        if spinning[i]:
            p = spin_progress[i]
            offset_y = math.sin(p * math.pi * 6) * 12 * (1 - p)
            scale = 1.0 + 0.07 * math.sin(p * math.pi * 10)

            img = symbols_info[reels[i]]["img"]
            scaled = pygame.transform.smoothscale(img, (int(SYMBOL_SIZE * scale), int(SYMBOL_SIZE * scale)))
            rect = scaled.get_rect(center=(cx, cy + offset_y))

            screen.blit(scaled, rect.topleft)
        else:
            screen.blit(symbols_info[reels[i]]["img"], (x, y_pos))

def draw_win_effect():
    global win_flash_timer, win_flash_active
    if last_win <= 0 or not win_flash_active:
        return

    win_flash_timer += 1
    if win_flash_timer > (200 if last_win >= 20 else 130):
        win_flash_active = False
        win_flash_timer = 0
        return

    flash_alpha = int(130 + 125 * math.sin(win_flash_timer * 0.35))
    win_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if last_win >= 20:
        txt = font_win.render(f"+{int(last_win)} SPINS!", True, (255, 215, 0))
        extra = font_big.render("MEGA WIN!", True, (255, 180, 60))
        extra.set_alpha(flash_alpha)
        win_surf.blit(extra, extra.get_rect(center=(WIDTH//2, HEIGHT//2 - 145)))
    else:
        txt = font_big.render(f"+{int(last_win)} SPINS", True, (200, 255, 180))

    txt.set_alpha(flash_alpha)
    rect = txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 35))
    win_surf.blit(txt, rect)

    screen.blit(win_surf, (0, 0))

def draw_button():
    btn_rect = pygame.Rect(WIDTH//2 - 160, HEIGHT - 150, 320, 105)
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
    pygame.draw.rect(screen, LIGHT_GOLD, btn_rect, width=6, border_radius=35)

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
        total_extra += 100
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

running = True
play_rect = None
spin_rect = None

while running:
    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:  
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
                        spins_left = 5
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