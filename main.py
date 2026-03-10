import os
import pygame

# See rida on vajalik, et pilves ei tekiks helivigu
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

pygame.init()
screen = pygame.display.set_mode((640, 360))
pygame.display.set_caption("Minu Pygame pilves")
backgroundImage = pygame.image.load("taust.png")

clock = pygame.time.Clock()
running = True

while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    #screen.fill((30, 30, 30)) # Tumehall taust
   # pygame.draw.circle(screen, (80, 200, 120), (320, 180), 60) # Roheline ring
    screen.blit(backgroundImage, (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()