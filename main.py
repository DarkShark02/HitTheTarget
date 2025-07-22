import cv2
import mediapipe as mp
import pygame
import sys
import math
import random
import time
import os

WIDTH, HEIGHT = 800, 600
RECORDS_FILE = "records.txt"
GAME_TIME = 60
TARGET_COUNT = 5

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
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
        self.lifetime = 10 if special else None
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
        color = (0, 255, 0) if self.special else (255, 100, 0)
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
    screen.blit(font.render("PARTITA FINITA!", True, (255, 255, 255)), (WIDTH//2 - 100, 100))
    screen.blit(font.render("\U0001F3C6 RECORD:", True, (255, 255, 0)), (WIDTH//2 - 60, 160))
    for i, (score, name, orange, green, combo) in enumerate(records):
        text = f"{i+1}. {name} - {score} pts | Arancioni: {orange} | Verdi: {green} | Combo: {combo}"
        screen.blit(font.render(text, True, (255, 255, 255)), (WIDTH//2 - 220, 200 + i*40))
    screen.blit(font.render("Alza il dito indice per giocare di nuovo", True, (150, 255, 150)), (WIDTH//2 - 220, 350))
    pygame.display.update()

def draw_text_centered(text, y, size=40, color=(255,255,255)):
    f = pygame.font.SysFont("Arial", size)
    surf = f.render(text, True, color)
    x = WIDTH//2 - surf.get_width()//2
    screen.blit(surf, (x, y))

def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, WIDTH)
    cap.set(4, HEIGHT)

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
        draw_text_centered("Inserisci il tuo nome e premi INVIO", HEIGHT//3)
        draw_text_centered(name, HEIGHT//2)
        pygame.display.update()
        clock.tick(30)

    min_x, max_x = 0.18, 0.92
    min_y, max_y = -0.13, 0.62
    print(f"Usando calibrazione fissa: X({min_x}, {max_x}), Y({min_y}, {max_y})")

    while True:
        punteggio = 0
        tempo_inizio = time.time()
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
                                punteggio += 10
                                green_hit_sound.play()
                                green_hits += 1
                            else:
                                punteggio += 1
                                hit_sound.play()
                                orange_hits += 1
                            now = time.time()
                            last_hits_times.append(now)
                            last_hits_times = [ht for ht in last_hits_times if now - ht <= 2]
                            if len(last_hits_times) >= 5:
                                if now - combo_cooldown > 1.5:
                                    combo_sound.play()
                                    punteggio += 5
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

            rimanente = max(0, GAME_TIME - int(time.time() - tempo_inizio))
            screen.blit(font.render(f"Tempo: {rimanente}", True, (255, 255, 255)), (10, 10))
            screen.blit(font.render(f"Punteggio: {punteggio}", True, (255, 255, 255)), (10, 50))
            screen.blit(font.render(f"Giocatore: {name}", True, (200, 200, 255)), (10, 90))
            
            # Legend in alto a destra
            legend_x = WIDTH - 180
            legend_y = 10

            # 1) Bersaglio arancione - 1 pt
            pygame.draw.circle(screen, (255, 100, 0), (legend_x, legend_y + 10), 10)
            screen.blit(font.render("1 pt", True, (255, 255, 255)), (legend_x + 25, legend_y))

            # 2) Combo - 5 pt con "esplosione" stilizzata (poligono stellato)
            def draw_star(surface, color, center, radius):
                points = []
                for i in range(10):
                    angle = i * math.pi / 5
                    r = radius if i % 2 == 0 else radius / 2
                    x = center[0] + r * math.cos(angle)
                    y = center[1] + r * math.sin(angle)
                    points.append((x, y))
                pygame.draw.polygon(surface, color, points)

            star_center = (legend_x, legend_y + 50)
            draw_star(screen, (255, 255, 0), star_center, 15)
            screen.blit(font.render("5 pt (COMBO)", True, (255, 255, 255)), (legend_x + 25, legend_y + 40))

            # 3) Bersaglio verde - 10 pt
            pygame.draw.circle(screen, (0, 255, 0), (legend_x, legend_y + 90), 10)
            screen.blit(font.render("10 pt", True, (255, 255, 255)), (legend_x + 25, legend_y + 80))

            if rimanente <= 0:
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

        records = save_score(punteggio, name, orange_hits, green_hits, combo_count)
        if punteggio > 0 and (len(old_scores) == 0 or punteggio > max(old_scores)):
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
