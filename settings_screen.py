import pygame
import json
from fetcher import generate_backtest_data
from config import GRAY, BLACK, WHITE, reload

SETTINGS_PATH = "settings.json"
with open(SETTINGS_PATH, "r") as f:
    settings = json.load(f)

pygame.init()
font = pygame.font.SysFont("arial", 30)
small_font = pygame.font.SysFont("arial", 22)


def flatten_settings(settings, exclude=None):
    exclude = exclude or []
    flat = {}
    for section, values in settings.items():
        if section in exclude:
            continue
        if isinstance(values, dict):
            for key, val in values.items():
                flat[f"{section}.{key}"] = val
        else:
            flat[section] = values
    return flat

def restore_settings(flat_settings):
    restored = {}
    for flat_key, value in flat_settings.items():
        keys = flat_key.split(".")
        d = restored
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
    return restored





def unflatten(d, sep='.'):
    result = {}
    for k, v in d.items():
        keys = k.split(sep)
        target = result
        for part in keys[:-1]:
            target = target.setdefault(part, {})
        target[keys[-1]] = v
    return result


def run_settings(screen):
    clock = pygame.time.Clock()
    flat = flatten_settings(settings, exclude=["coins.", "urls", "keys and secrets"])
    inputs = []

    scroll_y_start = 160  # just under the Generate Data area
    scroll_height = screen.get_height() - scroll_y_start - 80  # room for Save button
    for i, (key, val) in enumerate(flat.items()):
        rect = pygame.Rect(300, scroll_y_start + i * 40, 250, 30)  # offset for bottom half
        inputs.append([key, val, str(val), rect])

    save_button = pygame.Rect(200, screen.get_height() - 60, 200, 40)
    gen_button = pygame.Rect(30, 100, 250, 40)
    input_box = pygame.Rect(300, 100, 270, 40)
    input_active = False
    input_text = ""

    scroll = 0
    active_index = None

    while True:
        screen.fill(WHITE)
        y_offset = -scroll

        title = font.render("Settings", True, BLACK)
        screen.blit(title, (20, 10))

        pygame.draw.rect(screen, GRAY, gen_button)
        gen_label = small_font.render("Generate Data", True, BLACK)
        screen.blit(gen_label, (gen_button.x + 10, gen_button.y + 10))

        pygame.draw.rect(screen, WHITE, input_box)
        pygame.draw.rect(screen, BLACK, input_box, 2)
        input_label = small_font.render(input_text, True, BLACK)
        screen.blit(input_label, (input_box.x + 5, input_box.y + 10))
        clip_rect = pygame.Rect(0, scroll_y_start, screen.get_width(), scroll_height)

        screen.set_clip(clip_rect)

        for i, (key, val, text, rect) in enumerate(inputs):
            label = small_font.render(key, True, BLACK)
            screen.blit(label, (20, rect.y + y_offset))
            pygame.draw.rect(screen, WHITE, rect.move(0, y_offset))
            pygame.draw.rect(screen, BLACK, rect.move(0, y_offset), 2)
            text_surf = small_font.render(text, True, BLACK)
            screen.blit(text_surf, (rect.x + 5, rect.y + 5 + y_offset))

        pygame.draw.rect(screen, BLACK, clip_rect, 2)  # outline thickness = 2

        screen.set_clip(None)

        pygame.draw.rect(screen, (0, 200, 100), save_button)
        save_label = small_font.render("Save and Close", True, WHITE)
        screen.blit(save_label, (save_button.x + 20, save_button.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if gen_button.collidepoint(event.pos):
                    if input_text.isdigit():
                        generate_backtest_data(screen, int(input_text))

                elif input_box.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False

                if save_button.collidepoint(event.pos):
                    updated = {}
                    for key, _, text, _ in inputs:
                        try:
                            value = eval(text)
                        except:
                            value = text
                        updated[key] = value
                    restored = restore_settings(updated)

                    # Deep update only the edited parts
                    def deep_update(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict) and isinstance(d.get(k), dict):
                                deep_update(d[k], v)
                            else:
                                d[k] = v

                    deep_update(settings, restored)

                    # Then write to file
                    with open("settings.json", "w") as f:
                        json.dump(settings, f, indent=4)
                    return

                for i, (_, _, _, rect) in enumerate(inputs):
                    if rect.move(0, y_offset).collidepoint(event.pos):
                        active_index = i
                        break
                else:
                    active_index = None

            elif event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode.isdigit():
                        input_text += event.unicode

                elif active_index is not None:
                    key, old_val, text, rect = inputs[active_index]
                    if event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_index = None
                    else:
                        text += event.unicode
                    inputs[active_index][2] = text

            elif event.type == pygame.MOUSEWHEEL:
                scroll -= event.y * 30
                total_input_height = len(inputs) * 40
                visible_overlap = scroll_height // 2  # allows top to remain partially visible
                max_scroll = max(0, total_input_height - scroll_height + visible_overlap)
                scroll = max(0, min(scroll, max_scroll))

        clock.tick(30)
