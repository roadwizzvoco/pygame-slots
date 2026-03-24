import pygame
import random
import os
import sys
import math
from collections import Counter

# ==================== WINDOW CENTERING (works on local PC) ====================
# This tells SDL to automatically center the game window on your screen.
# No black bars, always windowed, fixed 1280×800 size.
os.environ['SDL_VIDEO_CENTERED'] = '1'
# =============================================================================

pygame.init()

WIDTH = 1280
HEIGHT = 800
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

BASE_SPIN_TIME = 550
EXTRA_DELAY_PER_REEL = 350
SYMBOL_SIZE = 160

LEFT_SHIFT = 80
PAYTABLE_RIGHT_OFFSET = 55
PAYTABLE_CONTENT_LEFT_OFFSET = -25
MENU_RIGHT_OFFSET = 35

current_path = os.path.dirname(os.path.abspath(__file__))

symbol_base_spins = {
    "7":      20,
    "GEM":    10,
    "CHERRY": 3,
    "BELL":   2,
    "COIN":   1,
    "BOMB":   0,
    "BONUS":  0,
}

font_title  = pygame.font.SysFont("georgia", 68, bold=True)
font_big    = pygame.font.SysFont("georgia", 48, bold=True)
font_med    = pygame.font.SysFont("georgia", 34, bold=True)
font_small  = pygame.font.SysFont("arial", 21)
font_button = pygame.font.SysFont("arialblack", 46, bold=True)
font_win    = pygame.font.SysFont("impact", 72, bold=True)


def weighted_random_symbol(symbols):
    r = random.random()
    cum = 0.0
    for i, s in enumerate(symbols):
        cum += s.prob
        if r < cum:
            return i
    return len(symbols) - 1


class Symbol:
    def __init__(self, file, name, prob):
        self.file = file
        self.name = name
        self.prob = prob
        self.base_spins = 0 if name == "BONUS" else symbol_base_spins.get(name, 0)
        self.img = None
        self.load_image()

    def load_image(self):
        try:
            img = pygame.image.load(os.path.join(current_path, self.file)).convert_alpha()
            self.img = pygame.transform.smoothscale(img, (SYMBOL_SIZE, SYMBOL_SIZE))
        except:
            self.img = pygame.Surface((SYMBOL_SIZE, SYMBOL_SIZE))
            self.img.fill((random.randint(120, 255), random.randint(80, 220), random.randint(60, 180)))

    def get_small_image(self, icon_size=70):
        return pygame.transform.smoothscale(self.img, (icon_size, icon_size))


class Reel:
    def __init__(self, reel_index):
        self.reel_index = reel_index
        self.symbol_index = 0
        self.spinning = False
        self.spin_progress = 0.0
        self.spin_start_time = 0
        self.spin_duration = 0

    def start_spin(self, duration):
        self.spinning = True
        self.spin_start_time = pygame.time.get_ticks()
        self.spin_duration = duration
        self.spin_progress = 0.0

    def update(self, current_time, symbols):
        if not self.spinning:
            return False
        elapsed = current_time - self.spin_start_time
        if elapsed < self.spin_duration:
            p = elapsed / self.spin_duration
            self.spin_progress = p
            if random.random() < (0.78 - p * 0.68):
                self.symbol_index = weighted_random_symbol(symbols)
            return True
        else:
            self.spin_progress = 1.0
            self.spinning = False
            return False

    def draw(self, screen, symbols, start_x, y_pos):
        x = start_x + self.reel_index * 265
        cx = x + SYMBOL_SIZE // 2
        cy = y_pos + SYMBOL_SIZE // 2

        if self.spinning:
            p = self.spin_progress
            offset_y = math.sin(p * math.pi * 6) * 12 * (1 - p)
            scale = 1.0 + 0.07 * math.sin(p * math.pi * 10)

            img = symbols[self.symbol_index].img
            scaled = pygame.transform.smoothscale(img, (int(SYMBOL_SIZE * scale), int(SYMBOL_SIZE * scale)))
            rect = scaled.get_rect(center=(cx, cy + offset_y))
            screen.blit(scaled, rect.topleft)
        else:
            screen.blit(symbols[self.symbol_index].img, (x, y_pos))


class Button:
    def __init__(self, x, y, width, height, text, base_color,
                 hover_color=None, press_color=None,
                 border_color=LIGHT_GOLD, text_color=WHITE,
                 draw_shadow=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color if hover_color is not None else BRIGHT_RED
        self.press_color = press_color if press_color is not None else (210, 40, 80)
        self.border_color = border_color
        self.text_color = text_color
        self.draw_shadow = draw_shadow
        self.shadow_offset = 8

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse)
        pressed = pygame.mouse.get_pressed()[0] and hovered

        if pressed:
            color = self.press_color
            shadow_off = 4
        elif hovered:
            color = self.hover_color
            shadow_off = self.shadow_offset
        else:
            color = self.base_color
            shadow_off = self.shadow_offset

        if self.draw_shadow:
            shadow_rect = self.rect.move(shadow_off, shadow_off)
            pygame.draw.rect(screen, (0, 0, 0, 180), shadow_rect, border_radius=35)

        pygame.draw.rect(screen, color, self.rect, border_radius=35)
        pygame.draw.rect(screen, self.border_color, self.rect, width=6, border_radius=35)

        t = font_button.render(self.text, True, self.text_color)
        screen.blit(t, t.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Paytable:
    def __init__(self, x, y, w, h, content_offset=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.content_offset = content_offset

    def draw(self, screen, symbols):
        glass = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        glass.fill(GLASS)
        pygame.draw.rect(glass, (80, 80, 120, 60), (0, 0, self.rect.width, self.rect.height), border_radius=22)
        screen.blit(glass, self.rect.topleft)
        pygame.draw.rect(screen, DARK_GOLD, self.rect, border_radius=22, width=4)

        y_off = self.rect.top + 70
        icon_size = 70

        for symb in symbols:
            small = symb.get_small_image(icon_size)
            screen.blit(small, (self.rect.left + 18 + self.content_offset, y_off + 8))

            name = font_small.render(symb.name, True, WHITE)
            screen.blit(name, (self.rect.left + 72 + self.content_offset, y_off + 10))

            if symb.name == "BONUS":
                desc = "+100 spins"
                col = (255, 220, 100)
            else:
                desc = f"+{symb.base_spins} spins"
                col = (180, 255, 180)

            d = font_small.render(desc, True, col)
            screen.blit(d, (self.rect.left + 72 + self.content_offset, y_off + 36))
            y_off += 72


class WinEffect:
    def __init__(self, left_shift=0):
        self.left_shift = left_shift
        self.last_win = 0
        self.flash_timer = 0
        self.active = False

    def trigger(self, amount):
        if amount > 0:
            self.last_win = amount
            self.active = True
            self.flash_timer = 0

    def update(self):
        if self.last_win <= 0 or not self.active:
            return
        self.flash_timer += 1
        limit = 200 if self.last_win >= 20 else 130
        if self.flash_timer > limit:
            self.active = False
            self.flash_timer = 0

    def draw(self, screen):
        if self.last_win <= 0 or not self.active:
            return

        flash_alpha = int(130 + 125 * math.sin(self.flash_timer * 0.35))
        win_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        center_x = WIDTH // 2 - self.left_shift

        if self.last_win >= 20:
            txt = font_win.render(f"+{int(self.last_win)} SPINS!", True, (255, 215, 0))
            extra = font_big.render("MEGA WIN!", True, (255, 180, 60))
            extra.set_alpha(flash_alpha)
            win_surf.blit(extra, extra.get_rect(center=(center_x, HEIGHT//2 - 145)))
        else:
            txt = font_big.render(f"+{int(self.last_win)} SPINS", True, (200, 255, 180))

        txt.set_alpha(flash_alpha)
        rect = txt.get_rect(center=(center_x, HEIGHT//2 - 35))
        win_surf.blit(txt, rect)
        screen.blit(win_surf, (0, 0))


class SlotMachine:
    def __init__(self):
        # ALWAYS WINDOWED + centered (no fullscreen ever)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Slot Machine")
        self.clock = pygame.time.Clock()

        self.left_shift = LEFT_SHIFT

        # Background (fills the entire 1280×800 window – no black bars)
        try:
            bg = pygame.image.load(os.path.join(current_path, "background.png")).convert()
            self.background_img = pygame.transform.smoothscale(bg, (WIDTH, HEIGHT))
        except:
            self.background_img = None

        # Symbols
        self.symbols = [
            Symbol("bonus.png",  "BONUS",  0.00536),
            Symbol("seitse.png", "7",      0.003568),
            Symbol("diamond.png","GEM",    0.010712),
            Symbol("cherry.png", "CHERRY", 0.035712),
            Symbol("bell.png",   "BELL",   0.05536),
            Symbol("coin.png",   "COIN",   0.089288),
            Symbol("bomb.png",   "BOMB",   0.80000),
        ]

        # Reels
        self.reels = [Reel(i) for i in range(3)]

        # UI elements
        self.play_button = Button(
            WIDTH//2 - 180 - self.left_shift + MENU_RIGHT_OFFSET, 380, 360, 110, "PLAY",
            RED, BRIGHT_RED, (210, 40, 80),
            LIGHT_GOLD, WHITE, draw_shadow=False
        )
        self.spin_button = Button(
            WIDTH//2 - 160 - self.left_shift, HEIGHT - 150, 320, 105, "SPIN",
            RED, BRIGHT_RED, (210, 40, 80),
            LIGHT_GOLD, WHITE, draw_shadow=True
        )
        self.paytable = Paytable(
            WIDTH - 225 - self.left_shift + PAYTABLE_RIGHT_OFFSET,
            60, 190, 630,
            content_offset=PAYTABLE_CONTENT_LEFT_OFFSET
        )
        self.win_effect = WinEffect(self.left_shift)

        self.spins_left = 5
        self.game_state = "MENU"

    def draw_background(self):
        if self.background_img:
            self.screen.blit(self.background_img, (0, 0))
        else:
            self.screen.fill(BLACK)

    def draw_menu(self):
        center_x = WIDTH // 2 - self.left_shift + MENU_RIGHT_OFFSET
        title = font_title.render("SLOT MACHINE", True, GOLD)
        title_rect = title.get_rect(center=(center_x, 160))
        self.screen.blit(title, title_rect.move(6, 6))
        self.screen.blit(title, title_rect)
        self.play_button.draw(self.screen)

    def draw_header(self):
        spins_rect = pygame.Rect(WIDTH//2 - 240 - self.left_shift, 25, 480, 70)
        pygame.draw.rect(self.screen, (20, 18, 45), spins_rect, border_radius=18)
        pygame.draw.rect(self.screen, DARK_GOLD, spins_rect, width=4, border_radius=18)
        spins_txt = font_med.render(f"SPINS LEFT: {self.spins_left}", True, LIGHT_GOLD)
        self.screen.blit(spins_txt, spins_txt.get_rect(center=spins_rect.center))

    def draw_slot_area(self):
        frame_rect = pygame.Rect(WIDTH//2 - 410 - self.left_shift, 155, 820, 410)
        pygame.draw.rect(self.screen, DARK_GOLD, frame_rect, border_radius=32, width=9)
        pygame.draw.rect(self.screen, GOLD, frame_rect, border_radius=32, width=3)
        inner = frame_rect.inflate(-24, -24)
        pygame.draw.rect(self.screen, (14, 12, 32), inner, border_radius=26)
        return inner

    def draw_reels(self, inner):
        start_x = inner.left + 85
        y_pos = inner.centery - SYMBOL_SIZE // 2 - 8
        for reel in self.reels:
            reel.draw(self.screen, self.symbols, start_x, y_pos)

    def draw_spin_button(self):
        if self.spins_left <= 0:
            self.spin_button.text = "RESTART"
            self.spin_button.base_color = GRAY
            self.spin_button.hover_color = GRAY
            self.spin_button.press_color = GRAY
        else:
            self.spin_button.text = "SPIN"
            self.spin_button.base_color = RED
            self.spin_button.hover_color = BRIGHT_RED
            self.spin_button.press_color = (210, 40, 80)
        self.spin_button.draw(self.screen)

    def start_spin(self):
        if self.spins_left <= 0 or any(reel.spinning for reel in self.reels):
            return
        self.win_effect.active = False
        self.win_effect.last_win = 0
        for i, reel in enumerate(self.reels):
            duration = BASE_SPIN_TIME + i * EXTRA_DELAY_PER_REEL + random.randint(-50, 50)
            reel.start_spin(duration)
        self.spins_left -= 1

    def update_reels(self):
        if not any(reel.spinning for reel in self.reels):
            return
        current_time = pygame.time.get_ticks()
        still_spinning = False
        for reel in self.reels:
            if reel.update(current_time, self.symbols):
                still_spinning = True
        if not still_spinning:
            self.check_win()

    def check_win(self):
        counts = Counter(reel.symbol_index for reel in self.reels)
        total_extra = 0
        bonus_count = 0
        for sym_idx, count in counts.items():
            sym = self.symbols[sym_idx]
            if sym.name == "BONUS":
                bonus_count = count
            else:
                total_extra += sym.base_spins * count
        if bonus_count == 3:
            total_extra += 100
        if total_extra > 0:
            self.spins_left += total_extra
            self.win_effect.trigger(total_extra)

    def run(self):
        running = True
        while running:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                    break

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == "MENU":
                        if self.play_button.handle_event(event):
                            self.game_state = "GAME"
                    else:
                        if self.spin_button.handle_event(event):
                            if self.spins_left > 0 and not any(reel.spinning for reel in self.reels):
                                self.start_spin()
                            elif self.spins_left <= 0:
                                self.spins_left = 5
                                self.win_effect.active = False
                                self.win_effect.last_win = 0
                                for reel in self.reels:
                                    reel.symbol_index = 0

            self.draw_background()

            if self.game_state == "MENU":
                self.draw_menu()
            else:
                self.draw_header()
                inner = self.draw_slot_area()
                self.draw_reels(inner)
                self.paytable.draw(self.screen, self.symbols)
                self.win_effect.update()
                self.win_effect.draw(self.screen)
                self.draw_spin_button()
                self.update_reels()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = SlotMachine()
    game.run()