import cv2
import mediapipe as mp
import pygame
import sys
import math
import random
import time
import os
import threading

WIDTH, HEIGHT = 800, 600
RECORDS_FILE = "records.txt"
GAME_TIME = 60
TARGET_COUNT = 5

ORANGE_POINTS = 1
GREEN_POINTS = 10
COMBO_POINTS = 5
COMBO_HITS = 5
COMBO_WINDOW = 2
GREEN_LIFETIME = 10

ORANGE = (255, 100, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hit The Target")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)

hit_sound = pygame.mixer.Sound("hit.wav")
combo_sound = pygame.mixer.Sound("combo.wav")
record_sound = pygame.mixer.Sound("record.wav")
green_hit_sound = pygame.mixer.Sound("green_hit.wav")


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def draw_cross(surface, pos, size=5, color=(255, 0, 0)):
    x, y = pos
    pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)

def draw_star(surface, color, center, radius):
    points = []
    for i in range(10):
        angle = i * math.pi / 5
        r = radius if i % 2 == 0 else radius / 2
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)

def remap(val, old_min, old_max, new_min, new_max):
    if old_max - old_min == 0:
        return new_min
    return new_min + (val - old_min) * (new_max - new_min) / (old_max - old_min)

def is_index_only_up(lm):
    def folded(a, b): return lm[a].y > lm[b].y
    return (
        lm[8].y < lm[6].y and
        folded(12, 10) and
        folded(16, 14) and
        folded(20, 18)
    )

class Target:
    def __init__(self, special=False):
        self.radius = 25 if special else 30
        self.pos = [random.randint(100, WIDTH - 100), random.randint(150, HEIGHT - 100)]
        self.special = special
        self.hit = False
        self.spawn_time = time.time()
        self.lifetime = GREEN_LIFETIME if special else None
        self.speed_x = random.choice([-15, 15]) if special else random.choice([-12, -10, -8, 8, 10, 12])
        self.speed_y = random.choice([-8, -6, 6, 8]) if special else random.choice([-6, -4, -2, 2, 4, 6])

    def update(self):
        if not self.hit:
            self.pos[0] += self.speed_x
            self.pos[1] += self.speed_y

            if self.pos[0] < self.radius or self.pos[0] > WIDTH - self.radius:
                self.speed_x *= -1
            if self.pos[1] < self.radius or self.pos[1] > HEIGHT - self.radius:
                self.speed_y *= -1

            if self.special and time.time() - self.spawn_time > self.lifetime:
                self.hit = True

    def draw(self, surf):
        color = GREEN if self.special else ORANGE
        if self.hit:
            color = (50, 100, 50) if self.special else (80, 80, 80)
        pygame.draw.circle(surf, color, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def check_hit(self, point):
        if not self.hit and distance(self.pos, point) < self.radius:
            self.hit = True
            return True
        return False

def check_target_collisions(targets):
    for i in range(len(targets)):
        for j in range(i+1, len(targets)):
            t1, t2 = targets[i], targets[j]
            if not t1.hit and not t2.hit:
                if distance(t1.pos, t2.pos) < t1.radius + t2.radius:
                    t1.speed_x, t2.speed_x = -t1.speed_x, -t2.speed_x
                    t1.speed_y, t2.speed_y = -t1.speed_y, -t2.speed_y

def spawn_target_non_overlapping(existing_targets, special=False, max_attempts=100):
    for _ in range(max_attempts):
        candidate = Target(special=special)
        if all(distance(candidate.pos, t.pos) > candidate.radius + t.radius + 10 for t in existing_targets if not t.hit):
            return candidate
    return candidate

def save_score(score, name, orange_hits, green_hits, combo_count):
    scores = []
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r") as f:
            for line in f:
                try:
                    parts = line.strip().split(",", 4)
                    s = int(parts[0])
                    n = parts[1]
                    o = int(parts[2]) if len(parts) > 2 else 0
                    g = int(parts[3]) if len(parts) > 3 else 0
                    c = int(parts[4]) if len(parts) > 4 else 0
                    scores.append((s, n, o, g, c))
                except:
                    continue
    scores.append((score, name, orange_hits, green_hits, combo_count))
    scores = sorted(scores, reverse=True, key=lambda x: x[0])[:3]
    with open(RECORDS_FILE, "w") as f:
        for s, n, o, g, c in scores:
            f.write(f"{s},{n},{o},{g},{c}\n")
    return scores

def show_records(records):
    screen.fill((0, 0, 0))
    draw_text_centered("GAME OVER!", 100, size=30)
    draw_text_centered("HIGH SCORES", 160, size=30, color=YELLOW)
    for i, (score, name, orange, green, combo) in enumerate(records):
        text = f"{i+1}. {name} - {score} pts | Orange: {orange} | Green: {green} | Combo: {combo}"
        draw_text_centered(text, 200 + i*40, size=24)
    draw_text_centered("Raise your index finger to play again", 350, size=30, color=(150, 255, 150))
    pygame.display.update()

def draw_text_centered(text, y, size=40, color=WHITE):
    f = pygame.font.SysFont("Arial", size)
    surf = f.render(text, True, color)
    x = WIDTH//2 - surf.get_width()//2
    screen.blit(surf, (x, y))

def draw_instructions(status, status_color):
    screen.fill((0, 0, 0))
    draw_text_centered("HIT THE TARGET", 40, size=56, color=YELLOW)

    draw_text_centered("HOW TO PLAY", 130, size=30, color=(150, 200, 255))
    draw_text_centered("Raise only your INDEX finger and touch the balls to pop them.", 175, size=24)
    draw_text_centered(f"Pop as many balls as you can in {GAME_TIME} seconds!", 210, size=24)

    draw_text_centered("POINTS", 270, size=30, color=(150, 200, 255))
    rows_x = 170
    item_font = pygame.font.SysFont("Arial", 24)

    pygame.draw.circle(screen, ORANGE, (rows_x, 330), 18)
    screen.blit(item_font.render(f"Orange ball:  {ORANGE_POINTS} pt", True, WHITE), (rows_x + 40, 316))

    pygame.draw.circle(screen, GREEN, (rows_x, 385), 16)
    screen.blit(item_font.render(f"Green ball (rare, fast, vanishes after {GREEN_LIFETIME}s):  {GREEN_POINTS} pts",
                                 True, WHITE), (rows_x + 40, 371))

    draw_star(screen, YELLOW, (rows_x, 440), 20)
    screen.blit(item_font.render(f"Combo ({COMBO_HITS} pops within {COMBO_WINDOW}s):  +{COMBO_POINTS} pts",
                                 True, WHITE), (rows_x + 40, 426))

    draw_text_centered(status, 520, size=30, color=status_color)
    pygame.display.update()

def load_resources():
    """Opens the camera and the hand tracking model while showing the instructions screen."""
    loaded = {}

    def worker():
        cap = cv2.VideoCapture(0)
        cap.set(3, WIDTH)
        cap.set(4, HEIGHT)
        hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        # The first frame processed is slow, so warm up the model here
        success, frame = cap.read()
        if success:
            hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        loaded["cap"] = cap
        loaded["hands"] = hands

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not thread.is_alive():
                return loaded["cap"], loaded["hands"]

        if thread.is_alive():
            dots = "." * (int(time.time() * 2) % 4)
            draw_instructions(f"Loading camera{dots}", (200, 200, 200))
        else:
            draw_instructions("Ready! Press ENTER to continue", (150, 255, 150))
        clock.tick(30)

def main():
    cap, hands = load_resources()

    name = ""
    input_active = True
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip() != "":
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 15 and event.unicode.isprintable():
                        name += event.unicode

        screen.fill((0,0,0))
        draw_text_centered("Enter your name and press ENTER", HEIGHT//3)
        draw_text_centered(name, HEIGHT//2)
        pygame.display.update()
        clock.tick(30)

    min_x, max_x = 0.18, 0.92
    min_y, max_y = -0.13, 0.62
    print(f"Using fixed calibration: X({min_x}, {max_x}), Y({min_y}, {max_y})")

    while True:
        score = 0
        start_time = time.time()
        targets = []
        last_hits_times = []
        combo_cooldown = 0
        orange_hits = 0
        green_hits = 0
        combo_count = 0


        for _ in range(TARGET_COUNT):
            if random.random() < 0.01:
                targets.append(spawn_target_non_overlapping(targets, special=True))
            else:
                targets.append(spawn_target_non_overlapping(targets))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.quit()
                    sys.exit()

            success, frame = cap.read()
            if not success:
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            screen.fill((0, 0, 0))

            for t in targets:
                t.update()
                t.draw(screen)

            check_target_collisions(targets)

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                lm = hand.landmark
                raw_x = lm[8].x
                raw_y = lm[8].y
                x = int(remap(raw_x, min_x, max_x, 0, WIDTH))
                y = int(remap(raw_y, min_y, max_y, 0, HEIGHT))
                x = max(0, min(WIDTH, x))
                y = max(0, min(HEIGHT, y))
                finger_pos = (x, y)

                if is_index_only_up(lm):
                    draw_cross(screen, finger_pos, size=10)
                    for t in targets:
                        if t.check_hit(finger_pos):
                            if t.special:
                                score += GREEN_POINTS
                                green_hit_sound.play()
                                green_hits += 1
                            else:
                                score += ORANGE_POINTS
                                hit_sound.play()
                                orange_hits += 1
                            now = time.time()
                            last_hits_times.append(now)
                            last_hits_times = [ht for ht in last_hits_times if now - ht <= COMBO_WINDOW]
                            if len(last_hits_times) >= COMBO_HITS:
                                if now - combo_cooldown > 1.5:
                                    combo_sound.play()
                                    score += COMBO_POINTS
                                    combo_count += 1
                                    combo_cooldown = now
                                last_hits_times.clear()
                            break

            targets = [t for t in targets if not t.hit]
            while len(targets) < TARGET_COUNT:
                if random.random() < 0.01:
                    targets.append(spawn_target_non_overlapping(targets, special=True))
                else:
                    targets.append(spawn_target_non_overlapping(targets))

            remaining = max(0, GAME_TIME - int(time.time() - start_time))
            screen.blit(font.render(f"Time: {remaining}", True, WHITE), (10, 10))
            screen.blit(font.render(f"Score: {score}", True, WHITE), (10, 50))
            screen.blit(font.render(f"Player: {name}", True, (200, 200, 255)), (10, 90))

            # Legend in the top right corner
            legend_x = WIDTH - 180
            legend_y = 10

            # 1) Orange target - 1 pt
            pygame.draw.circle(screen, ORANGE, (legend_x, legend_y + 10), 10)
            screen.blit(font.render(f"{ORANGE_POINTS} pt", True, WHITE), (legend_x + 25, legend_y))

            # 2) Combo - 5 pts, shown as a stylized "explosion" (star polygon)
            star_center = (legend_x, legend_y + 50)
            draw_star(screen, YELLOW, star_center, 15)
            screen.blit(font.render(f"{COMBO_POINTS} pt (COMBO)", True, WHITE), (legend_x + 25, legend_y + 40))

            # 3) Green target - 10 pts
            pygame.draw.circle(screen, GREEN, (legend_x, legend_y + 90), 10)
            screen.blit(font.render(f"{GREEN_POINTS} pt", True, WHITE), (legend_x + 25, legend_y + 80))

            if remaining <= 0:
                break

            pygame.display.update()
            clock.tick(60)

        old_scores = []
        if os.path.exists(RECORDS_FILE):
            with open(RECORDS_FILE, "r") as f:
                for line in f:
                    try:
                        s, _ = line.strip().split(",", 1)
                        old_scores.append(int(s))
                    except:
                        continue

        records = save_score(score, name, orange_hits, green_hits, combo_count)
        if score > 0 and (len(old_scores) == 0 or score > max(old_scores)):
            record_sound.play()

        show_records(records)
        pygame.time.delay(3000)

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.quit()
                    sys.exit()

            success, frame = cap.read()
            if not success:
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            screen.fill((0, 0, 0))
            show_records(records)

            if result.multi_hand_landmarks:
                lm = result.multi_hand_landmarks[0].landmark
                if is_index_only_up(lm):
                    waiting = False

            pygame.display.update()
            clock.tick(10)

if __name__ == "__main__":
    main()
