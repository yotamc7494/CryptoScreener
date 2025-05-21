import pygame
import sys
from fetcher import generate_backtest_data
from random_forest import recreate_model
from config import GRAY, LIGHT_GRAY, BLACK, WHITE

pygame.init()
font = pygame.font.SysFont("arial", 30)
small_font = pygame.font.SysFont("arial", 22)

class Button:
    def __init__(self, text, pos, callback, sizes=(300, 50), params=None):
        self.text = text
        self.pos = pos
        self.callback = callback
        self.params = params
        self.highlight = False
        self.rect = pygame.Rect(pos[0], pos[1], sizes[0], sizes[1])

    def draw(self, surface):
        color = LIGHT_GRAY if self.highlight else GRAY
        pygame.draw.rect(surface, color, self.rect)
        txt_surface = font.render(self.text, True, BLACK)
        surface.blit(txt_surface, (self.rect.x + (self.rect.width - txt_surface.get_width()) / 2,
                                   self.rect.y + 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.params:
                self.callback(self.params)
            else:
                self.callback()
        if event.type == 1024:  # MOUSEMOTION
            self.highlight = self.rect.collidepoint(event.pos)

def run_settings(screen):
    pygame.display.set_caption("Settings")
    clock = pygame.time.Clock()

    input_box = pygame.Rect(150, 200, 300, 40)
    input_text = ""
    input_active = False
    show_popup = False

    def open_popup():
        nonlocal show_popup
        show_popup = True

    def cancel_popup():
        nonlocal show_popup, input_text
        show_popup = False
        input_text = ""

    def confirm_popup():
        nonlocal input_text, show_popup
        if input_text.isdigit():
            generate_backtest_data(screen, int(input_text))
        show_popup = False
        input_text = ""

    buttons = [
        Button("Generate Data", (150, 100), open_popup),
        Button("Retrain RF", (150, 160), recreate_model, params=screen)
    ]

    cancel_btn = Button("Cancel", (120, 260), cancel_popup, sizes=(170, 50))
    confirm_btn = Button("Execute", (320, 260), confirm_popup, sizes=(170, 50))

    while True:
        screen.fill(WHITE)
        header = font.render("Settings", True, BLACK)
        width = header.get_width()
        screen.blit(header, ((screen.get_size()[0]/2)-(width/2), 50))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if show_popup:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint(event.pos):
                        input_active = True
                    else:
                        input_active = False
                elif event.type == pygame.KEYDOWN and input_active:
                    if event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode.isdigit() and len(input_text) < 6:
                        input_text += event.unicode
                cancel_btn.handle_event(event)
                confirm_btn.handle_event(event)
            else:
                for b in buttons:
                    b.handle_event(event)

        for b in buttons:
            b.draw(screen)

        if show_popup:
            # popup background
            pygame.draw.rect(screen, (220, 220, 220), (100, 150, 400, 180))
            pygame.draw.rect(screen, BLACK, (100, 150, 400, 180), 2)

            label = small_font.render("How many candles per coin?", True, BLACK)
            screen.blit(label, (300 - label.get_width() // 2, 160))

            pygame.draw.rect(screen, WHITE, input_box)
            pygame.draw.rect(screen, BLACK, input_box, 2)
            text_surface = small_font.render(input_text, True, BLACK)
            screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))

            cancel_btn.draw(screen)
            confirm_btn.draw(screen)

        pygame.display.flip()
        clock.tick(30)
