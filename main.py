"""
Flappy Shiba Inu  ·  Press SPACE to flap
"""
import io
import math
import os
import random
import struct
import sys
import wave

import pygame

# ─────────────────────────────────────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# ═════════════════════════════════════════════════════════════════════════════
#  CONFIG  ←  edit anything in this block to restyle or retune the game
# ═════════════════════════════════════════════════════════════════════════════

WINDOW_W = 480
WINDOW_H = 640
FPS      = 60

# Physics
GRAVITY      = 0.45
FLAP_FORCE   = -9.0
MAX_FALL_SPD = 12.0

# Pipes
PIPE_SPEED   = 3      # px / frame  (increase to make the game harder)
PIPE_GAP     = 150    # vertical gap between top and bottom pipe (px)
PIPE_WIDTH   = 70     # pipe width (px)
PIPE_CAP_H   = 28     # height of the wide cap at the pipe mouth (px)
PIPE_SPACING = 220    # horizontal distance between consecutive pipe pairs (px)

GROUND_H = 80         # ground strip height (px)

# ── Colours  ←  change any of these to restyle ──────────────────────────────
BG_TOP          = (112, 197, 206)   # sky gradient – top colour
BG_BOTTOM       = (160, 220, 230)   # sky gradient – bottom colour
GROUND_COLOR    = (222, 184, 135)
GROUND_LINE     = (180, 140,  90)
PIPE_BODY       = (  0, 180,   0)   # ← main pipe body colour
PIPE_BORDER     = (  0, 120,   0)   # ← pipe border / outline colour
PIPE_CAP        = (  0, 210,   0)   # ← pipe cap (mouth) colour
SCORE_COLOR     = (255, 255, 255)
SCORE_SHADOW    = ( 60,  60,  60)
SHIBA_FALLBACK  = (210, 140,  60)   # placeholder colour when no image found

# Fireworks (active when score >= FIREWORK_THRESHOLD)
FIREWORK_THRESHOLD = 100
FIREWORK_RATE      = 0.04           # probability per frame of a new burst
FIREWORK_COLORS    = [
    (255,  80,  80), (255, 220,  60), ( 80, 255, 120),
    ( 80, 160, 255), (255,  80, 255), (255, 255,  80),
]

# ── Shiba image ───────────────────────────────────────────────────────────────
#
#   HOW TO ADD YOUR SHIBA IMAGE
#   ───────────────────────────
#   1. Name your file exactly:  shiba.png
#   2. Copy it into the assets/ folder next to this script:
#          flappyShibaInu/
#          ├── main.py
#          └── assets/
#              └── shiba.png   ← your file goes here
#   3. The image will be scaled to SHIBA_W × SHIBA_H pixels.
#      A square PNG with a transparent background works best.
#   4. If the file is missing, the game runs fine with a coloured rectangle.
#
#   After building the .exe (run build.bat), copy the assets/ folder so it
#   sits next to FlappyShibaInu.exe in the dist/ folder.
#
if getattr(sys, "frozen", False):       # running as compiled .exe
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

SHIBA_IMG_PATH = os.path.join(_BASE, "assets", "shiba.jfif")
SHIBA_W, SHIBA_H = 48, 48

# ─────────────────────────────────────────────────────────────────────────────
#  BARK SOUND  (generated in-code — no audio file needed)
# ─────────────────────────────────────────────────────────────────────────────

def _build_bark():
    rate   = 44100
    dur    = 0.14
    n      = int(rate * dur)
    rng    = random.Random(42)      # fixed seed → same sound every run
    frames = []
    for i in range(n):
        t   = i / rate
        env = math.exp(-t * 30)     # fast-decay envelope
        v   = (
            math.sin(2 * math.pi * 900 * t) * 0.40 +
            math.sin(2 * math.pi * 450 * t) * 0.25 +
            (rng.random() * 2 - 1)           * 0.30
        ) * env
        s = max(-32767, min(32767, int(v * 32767)))
        frames.append(struct.pack("<h", s))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))
    buf.seek(0)
    return pygame.mixer.Sound(file=buf)


# ─────────────────────────────────────────────────────────────────────────────
#  GAME OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

class ShibaInu:
    def __init__(self, img):
        self.img   = img
        self.x     = WINDOW_W // 4
        self.y     = float(WINDOW_H // 2)
        self.vel   = 0.0
        self.angle = 0.0
        self._sync_rect()

    def _sync_rect(self):
        self.rect = pygame.Rect(
            self.x - SHIBA_W // 2,
            int(self.y) - SHIBA_H // 2,
            SHIBA_W, SHIBA_H,
        )

    def flap(self):
        self.vel = FLAP_FORCE

    def update(self):
        self.vel   = min(self.vel + GRAVITY, MAX_FALL_SPD)
        self.y    += self.vel
        target     = max(-30.0, min(90.0, self.vel * 6.0))
        self.angle += (target - self.angle) * 0.2
        self._sync_rect()

    def draw(self, surf):
        if self.img:
            rotated = pygame.transform.rotate(self.img, -self.angle)
            surf.blit(rotated, rotated.get_rect(center=(self.x, int(self.y))))
        else:
            # Fallback: coloured rectangle with simple face
            pygame.draw.rect(surf, SHIBA_FALLBACK, self.rect, border_radius=8)
            cx, cy = self.x, int(self.y)
            pygame.draw.circle(surf, (40,  20,   0), (cx - 10, cy - 5),  4)  # left eye
            pygame.draw.circle(surf, (40,  20,   0), (cx + 10, cy - 5),  4)  # right eye
            pygame.draw.circle(surf, (180,  80,  60), (cx,      cy + 7),  6)  # nose

    @property
    def dead(self):
        return self.y < 0 or self.y > WINDOW_H - GROUND_H


class Pipe:
    def __init__(self, x):
        margin     = PIPE_GAP // 2 + 50
        self.gap_y = random.randint(margin, WINDOW_H - GROUND_H - margin)
        self.x     = float(x)
        self.scored = False

    @property
    def top_rect(self):
        h = self.gap_y - PIPE_GAP // 2
        return pygame.Rect(int(self.x), 0, PIPE_WIDTH, max(0, h))

    @property
    def bot_rect(self):
        top = self.gap_y + PIPE_GAP // 2
        return pygame.Rect(int(self.x), top, PIPE_WIDTH, max(0, WINDOW_H - GROUND_H - top))

    def update(self):
        self.x -= PIPE_SPEED

    @property
    def offscreen(self):
        return self.x + PIPE_WIDTH < 0

    def collides(self, shiba):
        hitbox = shiba.rect.inflate(-10, -10)   # slightly forgiving
        return hitbox.colliderect(self.top_rect) or hitbox.colliderect(self.bot_rect)

    def draw(self, surf):
        for rect in (self.top_rect, self.bot_rect):
            if rect.height <= 0:
                continue
            pygame.draw.rect(surf, PIPE_BODY,   rect)
            pygame.draw.rect(surf, PIPE_BORDER, rect, 3)
        self._draw_cap(surf, self.top_rect, at_bottom=True)
        self._draw_cap(surf, self.bot_rect, at_bottom=False)

    def _draw_cap(self, surf, pipe_rect, at_bottom):
        if pipe_rect.height <= 0:
            return
        cap = pygame.Rect(
            int(self.x) - 5,
            pipe_rect.bottom - PIPE_CAP_H if at_bottom else pipe_rect.top,
            PIPE_WIDTH + 10,
            PIPE_CAP_H,
        )
        pygame.draw.rect(surf, PIPE_CAP,    cap)
        pygame.draw.rect(surf, PIPE_BORDER, cap, 3)


class Particle:
    def __init__(self, x, y, color):
        angle     = random.uniform(0, 2 * math.pi)
        speed     = random.uniform(2, 8)
        self.x    = float(x)
        self.y    = float(y)
        self.vx   = math.cos(angle) * speed
        self.vy   = math.sin(angle) * speed
        self.col  = color
        self.life = random.randint(30, 60)
        self.max  = self.life
        self.r    = random.randint(2, 5)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.15
        self.vx *= 0.98
        self.life -= 1

    @property
    def dead(self):
        return self.life <= 0

    def draw(self, surf):
        alpha  = int(255 * self.life / self.max)
        radius = max(1, int(self.r * self.life / self.max))
        tmp    = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (*self.col, alpha), (radius, radius), radius)
        surf.blit(tmp, (int(self.x) - radius, int(self.y) - radius))


# ─────────────────────────────────────────────────────────────────────────────
#  GAME
# ─────────────────────────────────────────────────────────────────────────────

class Game:
    MENU    = 0
    PLAYING = 1
    DEAD    = 2

    def __init__(self):
        self.screen   = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Flappy Shiba Inu")
        self.clock    = pygame.time.Clock()
        self.font_big = pygame.font.SysFont(None, 72)
        self.font_med = pygame.font.SysFont(None, 40)
        self.font_sm  = pygame.font.SysFont(None, 28)

        self.shiba_img = self._load_shiba()
        self.bark      = self._load_bark()
        self._bg       = self._build_bg()

        self.state = self.MENU
        self._reset()

    # ── setup ────────────────────────────────────────────────────────────────

    def _load_shiba(self):
        if os.path.exists(SHIBA_IMG_PATH):
            img = pygame.image.load(SHIBA_IMG_PATH).convert_alpha()
            return pygame.transform.smoothscale(img, (SHIBA_W, SHIBA_H))
        return None

    def _load_bark(self):
        try:
            return _build_bark()
        except Exception:
            return None

    def _build_bg(self):
        surf = pygame.Surface((WINDOW_W, WINDOW_H - GROUND_H))
        sky_h = WINDOW_H - GROUND_H
        for y in range(sky_h):
            t = y / max(1, sky_h - 1)
            c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
            pygame.draw.line(surf, c, (0, y), (WINDOW_W, y))
        return surf

    def _reset(self):
        self.shiba      = ShibaInu(self.shiba_img)
        self.pipes      = []
        self.particles  = []
        self.score      = 0
        self.pipe_timer = 0

    # ── main loop ────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._events()
            if self.state == self.PLAYING:
                self._update()
            self._draw()

    def _events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.state == self.MENU:
                    self.state = self.PLAYING
                    self._flap()
                elif self.state == self.PLAYING:
                    self._flap()
                elif self.state == self.DEAD:
                    self._reset()
                    self.state = self.PLAYING

    def _flap(self):
        self.shiba.flap()
        if self.bark:
            self.bark.play()

    # ── update ───────────────────────────────────────────────────────────────

    def _update(self):
        self.shiba.update()

        self.pipe_timer += 1
        if self.pipe_timer >= max(1, PIPE_SPACING // PIPE_SPEED):
            self.pipe_timer = 0
            self.pipes.append(Pipe(WINDOW_W + 10))

        for pipe in self.pipes:
            pipe.update()
            if not pipe.scored and pipe.x + PIPE_WIDTH // 2 < self.shiba.x:
                pipe.scored = True
                self.score += 1

        self.pipes = [p for p in self.pipes if not p.offscreen]

        if self.shiba.dead:
            self.state = self.DEAD
        for pipe in self.pipes:
            if pipe.collides(self.shiba):
                self.state = self.DEAD

        if self.score >= FIREWORK_THRESHOLD and random.random() < FIREWORK_RATE:
            self._burst()

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if not p.dead]

    def _burst(self):
        x   = random.randint(60, WINDOW_W - 60)
        y   = random.randint(60, (WINDOW_H - GROUND_H) // 2)
        col = random.choice(FIREWORK_COLORS)
        self.particles.extend(Particle(x, y, col) for _ in range(40))

    # ── draw ─────────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.blit(self._bg, (0, 0))
        for p in self.particles:
            p.draw(self.screen)
        for pipe in self.pipes:
            pipe.draw(self.screen)
        self._draw_ground()
        self.shiba.draw(self.screen)
        self._draw_score()
        if self.state == self.MENU:
            self._draw_overlay([
                ("Flappy Shiba Inu",     self.font_big, (255, 220,  60)),
                ("Press SPACE to start", self.font_med, (255, 255, 255)),
            ])
        elif self.state == self.DEAD:
            self._draw_overlay([
                ("Arf!  Game Over",    self.font_big, (255,  80,  80)),
                (f"Score: {self.score}", self.font_med, (255, 255, 255)),
                ("SPACE to try again", self.font_sm,  (200, 200, 200)),
            ])
        pygame.display.flip()

    def _draw_ground(self):
        r = pygame.Rect(0, WINDOW_H - GROUND_H, WINDOW_W, GROUND_H)
        pygame.draw.rect(self.screen, GROUND_COLOR, r)
        pygame.draw.line(self.screen, GROUND_LINE,
                         (0, WINDOW_H - GROUND_H), (WINDOW_W, WINDOW_H - GROUND_H), 4)

    def _draw_score(self):
        txt = str(self.score)
        sh  = self.font_big.render(txt, True, SCORE_SHADOW)
        lb  = self.font_big.render(txt, True, SCORE_COLOR)
        x   = WINDOW_W // 2 - lb.get_width() // 2
        self.screen.blit(sh, (x + 2, 22))
        self.screen.blit(lb, (x,     20))

    def _draw_overlay(self, lines):
        ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 130))
        self.screen.blit(ov, (0, 0))
        surfs  = [font.render(text, True, col) for text, font, col in lines]
        gap    = 14
        total  = sum(s.get_height() for s in surfs) + gap * (len(surfs) - 1)
        y      = WINDOW_H // 2 - total // 2
        for s in surfs:
            self.screen.blit(s, (WINDOW_W // 2 - s.get_width() // 2, y))
            y += s.get_height() + gap


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
