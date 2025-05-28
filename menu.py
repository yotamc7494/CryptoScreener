import pygame
import sys
from config import GRAY, LIGHT_GRAY, BLACK, WHITE, WIDTH, HEIGHT
from screener import run_screener
from backtest import run_backtest
from settings_screen import run_settings


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crypto Screener Menu")
font = pygame.font.SysFont("arial", 30)
clock = pygame.time.Clock()

class Button:
    def __init__(self, text, pos, callback):
        self.text = text
        self.pos = pos
        self.callback = callback
        self.highlight = False
        self.rect = pygame.Rect(pos[0], pos[1], 300, 50)

    def draw(self, surface):
        color = GRAY
        if self.highlight:
            color = LIGHT_GRAY
        pygame.draw.rect(surface, color, self.rect)
        txt_surface = font.render(self.text, True, BLACK)
        text_width = txt_surface.get_size()[0]
        surface.blit(txt_surface, (self.rect.x + self.rect.width/2 - text_width/2, self.rect.y + 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
        if event.type == 1024:
            self.highlight = self.rect.collidepoint(event.pos)

def start_screener():
    run_screener(screen)

def backtest():
    run_backtest(screen)

def settings():
    run_settings(screen)

def quit_app():
    pygame.quit()
    sys.exit()

def start_menu():
    while True:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_app()
            for button in buttons:
                button.handle_event(event)

        for button in buttons:
            button.draw(screen)

        pygame.display.flip()
        clock.tick(60)

buttons = [
    Button("Start Screener", (150, 100), start_screener),
    Button("Backtest", (150, 160), backtest),
    Button("Settings", (150, 220), settings),
    Button("Quit", (150, 280), quit_app)
]
