import random
import pygame

# --- Configuration ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
WORLD_WIDTH = 3600
FPS = 60
ROUND_DURATION_SEC = 180  # 3-minute survival timer

# Colors (Vector-Neon Palette)
BG_COLOR = (8, 10, 18)
SHIP_COLOR = (0, 255, 220)
THRUST_COLOR = (255, 100, 50)
BOOST_FLAME_COLOR = (140, 255, 255)
LASER_COLOR = (255, 240, 90)
LANDER_COLOR = (255, 65, 105)
CHARGER_COLOR = (255, 145, 40)
BEACON_COLOR = (60, 255, 150)
BEACON_WARN_COLOR = (255, 210, 60)
CRATER_COLOR = (70, 80, 95)
TERRAIN_COLOR = (40, 200, 120)
TERRAIN_GLOW = (15, 70, 45)
HUD_BG = (15, 18, 30)
HUD_BORDER = (0, 180, 160)


def wrap_delta(target_x: float, origin_x: float) -> float:
    """Shortest signed horizontal distance from origin_x to target_x across WORLD_WIDTH."""
    dx = (target_x - origin_x) % WORLD_WIDTH
    if dx > WORLD_WIDTH / 2:
        dx -= WORLD_WIDTH
    return dx


class ImpactRing:
    """Expanding vector ring for enemy kills and beacon hits."""
    def __init__(self, x: float, y: float, color: tuple[int, int, int], max_radius: float = 42.0):
        self.pos = pygame.math.Vector2(x, y)
        self.color = color
        self.radius = 4.0
        self.max_radius = max_radius
        self.alive = True

    def update(self):
        self.radius += 2.6
        if self.radius >= self.max_radius:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: float):
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        if -60 <= screen_x <= SCREEN_WIDTH + 60:
            pygame.draw.circle(surface, self.color, (int(screen_x), int(self.pos.y)), int(self.radius), width=2)


class GroundBeacon:
    """Stationary ground energy base that enemies dive to destroy."""
    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.alive = True
        self.under_attack = False
        self.width = 26
        self.height = 24

    def draw(self, surface: pygame.Surface, camera_x: float, ticks: int):
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        if -50 <= screen_x <= SCREEN_WIDTH + 50:
            cx, by = int(screen_x), int(self.pos.y)

            if not self.alive:
                # Draw destroyed base rubble marker
                pygame.draw.line(surface, CRATER_COLOR, (cx - 12, by), (cx - 4, by - 6), 2)
                pygame.draw.line(surface, CRATER_COLOR, (cx + 4, by - 6), (cx + 12, by), 2)
                return

            blink = (ticks // 140) % 2 == 0
            color = BEACON_WARN_COLOR if (self.under_attack and blink) else BEACON_COLOR

            base_pts = [
                (cx - self.width // 2, by),
                (cx + self.width // 2, by),
                (cx + 6, by - self.height),
                (cx - 6, by - self.height),
            ]
            pygame.draw.polygon(surface, color, base_pts, width=2)

            pulse_radius = 4 if (ticks // 250) % 2 == 0 else 5
            pygame.draw.circle(surface, (220, 255, 240), (cx, by - self.height - 8), pulse_radius)


class LaserBolt:
    def __init__(self, x: float, y: float, facing: int):
        self.pos = pygame.math.Vector2(x, y)
        self.facing = facing
        self.speed = 24.0
        self.length = 34
        self.distance_traveled = 0.0
        self.max_distance = 750.0
        self.alive = True

    def update(self):
        step = self.speed * self.facing
        self.pos.x = (self.pos.x + step) % WORLD_WIDTH
        self.distance_traveled += abs(step)
        if self.distance_traveled >= self.max_distance:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: float):
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        if -50 <= screen_x <= SCREEN_WIDTH + 50:
            end_x = screen_x - (self.length * self.facing)
            pygame.draw.line(surface, (255, 170, 40), (screen_x, self.pos.y), (end_x, self.pos.y), 4)
            pygame.draw.line(surface, LASER_COLOR, (screen_x, self.pos.y), (end_x, self.pos.y), 2)


class LanderEnemy:
    """
    Enemy AI that spawns high in the sky, locks onto a living GroundBeacon,
    and dives toward it to destroy it on contact.
    """
    def __init__(self, radar_height: int, beacons: list[GroundBeacon], speed_mult: float, is_charger: bool = False):
        self.is_charger = is_charger
        self.pos = pygame.math.Vector2(
            random.uniform(0, WORLD_WIDTH),
            radar_height + random.uniform(22, 48),
        )
        self.radius = 14 if is_charger else 16
        self.points_value = 250 if is_charger else 100
        self.alive = True
        self.destroyed_beacon = False
        self.target_beacon: GroundBeacon | None = None
        self.base_speed = (2.7 if is_charger else 1.75) * speed_mult
        self.pick_target(beacons)

    def pick_target(self, beacons: list[GroundBeacon]):
        living = [b for b in beacons if b.alive]
        if not living:
            self.target_beacon = None
            return
        if self.is_charger:
            self.target_beacon = random.choice(living)
        else:
            self.target_beacon = min(living, key=lambda b: abs(wrap_delta(b.pos.x, self.pos.x)))

    def update(self, beacons: list[GroundBeacon]):
        if not self.target_beacon or not self.target_beacon.alive:
            self.pick_target(beacons)

        if self.target_beacon:
            dx = wrap_delta(self.target_beacon.pos.x, self.pos.x)
            dy = (self.target_beacon.pos.y - 10) - self.pos.y

            vx = max(-self.base_speed * 1.15, min(self.base_speed * 1.15, dx * 0.03))
            vy = self.base_speed * (0.95 if abs(dx) < 120 else 0.55)

            self.pos.x = (self.pos.x + vx) % WORLD_WIDTH
            self.pos.y += vy

            if abs(dx) < 110 and dy < 210:
                self.target_beacon.under_attack = True

            # Impact with target beacon
            if abs(dx) < 20 and abs(dy) < 18:
                self.target_beacon.alive = False
                self.destroyed_beacon = True
                self.alive = False
        else:
            self.pos.y += self.base_speed

    def draw(self, surface: pygame.Surface, camera_x: float):
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        if -40 <= screen_x <= SCREEN_WIDTH + 40:
            cx, cy = int(screen_x), int(self.pos.y)
            r = self.radius

            # Draw faint dive-lock sightline when closing in on a beacon
            if self.target_beacon and self.target_beacon.alive:
                bx = SCREEN_WIDTH / 2 + wrap_delta(self.target_beacon.pos.x, camera_x)
                by = self.target_beacon.pos.y - 12
                if abs(bx - cx) < 130 and (by - cy) < 220:
                    pygame.draw.line(surface, (90, 35, 50), (cx, cy + r), (int(bx), int(by)), 1)

            if self.is_charger:
                pts = [(cx, cy + r + 3), (cx + r, cy - r), (cx, cy - r // 2), (cx - r, cy - r)]
                pygame.draw.polygon(surface, CHARGER_COLOR, pts, width=2)
                pygame.draw.circle(surface, (255, 230, 180), (cx, cy), 3)
            else:
                pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
                pygame.draw.polygon(surface, LANDER_COLOR, pts, width=2)
                pygame.draw.line(surface, LANDER_COLOR, (cx - 8, cy + r - 3), (cx - 13, cy + r + 5), 2)
                pygame.draw.line(surface, LANDER_COLOR, (cx + 8, cy + r - 3), (cx + 13, cy + r + 5), 2)


class PlayerShip:
    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.facing = 1
        self.base_accel = 0.65
        self.friction = 0.92
        self.base_max_speed = 9.0
        self.boost_max_speed = 17.5
        self.width = 36
        self.height = 16
        self.fire_cooldown = 140
        self.last_shot_time = 0
        self.invuln_until = 0

        # Double-tap boost state
        self.double_tap_window = 250
        self.boost_duration = 350
        self.boost_cooldown = 600
        self.last_tap_dir = 0
        self.last_tap_time = 0
        self.boost_until = 0
        self.next_boost_allowed = 0
        self.afterimages: list[tuple[float, float, int, int]] = []

    def handle_keydown(self, key: int, now: int):
        tap_dir = 0
        if key in (pygame.K_LEFT, pygame.K_a):
            tap_dir = -1
        elif key in (pygame.K_RIGHT, pygame.K_d):
            tap_dir = 1

        if tap_dir != 0:
            if (
                tap_dir == self.last_tap_dir
                and (now - self.last_tap_time) <= self.double_tap_window
                and now >= self.next_boost_allowed
            ):
                self.facing = tap_dir
                self.boost_until = now + self.boost_duration
                self.next_boost_allowed = self.boost_until + self.boost_cooldown
                self.vel.x = tap_dir * self.boost_max_speed
                self.last_tap_dir = 0
            else:
                self.last_tap_dir = tap_dir
                self.last_tap_time = now

    def is_boosting(self, now: int) -> bool:
        return now < self.boost_until

    def update(self, keys: pygame.key.ScancodeWrapper, top_bound: int, bottom_bound: int, now: int):
        move_x = (1 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0) - (
            1 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0
        )
        move_y = (1 if (keys[pygame.K_DOWN] or keys[pygame.K_s]) else 0) - (
            1 if (keys[pygame.K_UP] or keys[pygame.K_w]) else 0
        )

        if move_x != 0:
            self.facing = move_x

        boosting = self.is_boosting(now)
        accel = self.base_accel * (1.85 if boosting else 1.0)
        max_speed = self.boost_max_speed if boosting else self.base_max_speed

        drive_x = self.facing if boosting else move_x
        self.vel.x = (self.vel.x + drive_x * accel) * self.friction
        self.vel.y = (self.vel.y + move_y * self.base_accel) * self.friction

        if self.vel.length() > max_speed:
            self.vel.scale_to_length(max_speed)

        self.pos.x = (self.pos.x + self.vel.x) % WORLD_WIDTH
        self.pos.y = max(top_bound, min(bottom_bound, self.pos.y + self.vel.y))

        if boosting:
            self.afterimages.append((self.pos.x, self.pos.y, self.facing, now + 140))
        self.afterimages = [img for img in self.afterimages if img[3] > now]

    def try_fire(self, current_time: int) -> LaserBolt | None:
        if current_time - self.last_shot_time >= self.fire_cooldown:
            self.last_shot_time = current_time
            nose_x = (self.pos.x + (self.width / 2) * self.facing) % WORLD_WIDTH
            return LaserBolt(nose_x, self.pos.y, self.facing)
        return None

    def _get_hull_points(self, screen_x: float, screen_y: float, facing: int):
        nose = (screen_x + (self.width / 2) * facing, screen_y)
        top_wing = (screen_x - (self.width / 2) * facing, screen_y - self.height / 2)
        bottom_wing = (screen_x - (self.width / 2) * facing, screen_y + self.height / 2)
        notch = (screen_x - (self.width / 4) * facing, screen_y)
        return nose, top_wing, notch, bottom_wing

    def draw(self, surface: pygame.Surface, camera_x: float, now: int):
        if now < self.invuln_until and (now // 80) % 2 == 0:
            return

        for ax, ay, afacing, _ in self.afterimages:
            asx = SCREEN_WIDTH / 2 + wrap_delta(ax, camera_x)
            if -50 <= asx <= SCREEN_WIDTH + 50:
                pts = self._get_hull_points(asx, ay, afacing)
                pygame.draw.polygon(surface, (0, 110, 120), pts, width=1)

        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        screen_y = self.pos.y
        nose, top_wing, notch, bottom_wing = self._get_hull_points(screen_x, screen_y, self.facing)

        boosting = self.is_boosting(now)
        if boosting or self.vel.length() > 1.5:
            flame_len = random.uniform(24, 38) if boosting else random.uniform(10, 22)
            flame_col = BOOST_FLAME_COLOR if boosting else THRUST_COLOR
            flame_tip = (screen_x - (self.width / 2 + flame_len) * self.facing, screen_y)
            pygame.draw.polygon(surface, flame_col, [top_wing, notch, bottom_wing, flame_tip])

        pygame.draw.polygon(surface, SHIP_COLOR, [nose, top_wing, notch, bottom_wing], width=2)


class WorldBackdrop:
    def __init__(self, radar_height: int):
        self.radar_height = radar_height
        self.stars = [
            (
                random.uniform(0, WORLD_WIDTH),
                random.uniform(radar_height + 10, SCREEN_HEIGHT - 120),
                random.choice([0.3, 0.6, 1.0]),
                random.randint(90, 220),
            )
            for _ in range(140)
        ]

        self.segment_width = 75
        num_segments = WORLD_WIDTH // self.segment_width
        self.terrain_points = [
            (i * self.segment_width, SCREEN_HEIGHT - random.randint(40, 105))
            for i in range(num_segments)
        ]

    def get_terrain_y(self, world_x: float) -> float:
        wx = world_x % WORLD_WIDTH
        idx = int(wx // self.segment_width)
        next_idx = (idx + 1) % len(self.terrain_points)
        x1, y1 = self.terrain_points[idx]
        _, y2 = self.terrain_points[next_idx]
        t = (wx - x1) / self.segment_width
        return y1 + (y2 - y1) * t

    def draw(self, surface: pygame.Surface, camera_x: float):
        for star_x, star_y, parallax, brightness in self.stars:
            effective_cam = (camera_x * parallax) % WORLD_WIDTH
            sx = SCREEN_WIDTH / 2 + wrap_delta(star_x, effective_cam)
            if 0 <= sx <= SCREEN_WIDTH:
                color = (brightness, brightness, min(255, brightness + 30))
                size = 2 if parallax == 1.0 else 1
                pygame.draw.rect(surface, color, (sx, star_y, size, size))

        visible_points = []
        for world_x, world_y in self.terrain_points:
            sx = SCREEN_WIDTH / 2 + wrap_delta(world_x, camera_x)
            if -self.segment_width * 2 <= sx <= SCREEN_WIDTH + self.segment_width * 2:
                visible_points.append((sx, world_y))

        visible_points.sort(key=lambda p: p[0])

        if len(visible_points) >= 2:
            glow_points = [(x, y + 3) for x, y in visible_points]
            pygame.draw.lines(surface, TERRAIN_GLOW, False, glow_points, width=5)
            pygame.draw.lines(surface, TERRAIN_COLOR, False, visible_points, width=2)


def draw_scanner_hud(
    surface: pygame.Surface,
    player: PlayerShip,
    beacons: list[GroundBeacon],
    enemies: list[LanderEnemy],
    lasers: list[LaserBolt],
    camera_x: float,
    radar_height: int,
    ticks: int,
):
    pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_WIDTH, radar_height))
    pygame.draw.line(surface, HUD_BORDER, (0, radar_height), (SCREEN_WIDTH, radar_height), 2)

    radar_w = 460
    radar_h = radar_height - 16
    radar_x = (SCREEN_WIDTH - radar_w) // 2
    radar_y = 8
    pygame.draw.rect(surface, (10, 14, 24), (radar_x, radar_y, radar_w, radar_h))
    pygame.draw.rect(surface, HUD_BORDER, (radar_x, radar_y, radar_w, radar_h), 1)

    view_w = (SCREEN_WIDTH / WORLD_WIDTH) * radar_w
    cam_radar_x = radar_x + ((camera_x - SCREEN_WIDTH / 2) % WORLD_WIDTH) / WORLD_WIDTH * radar_w

    if cam_radar_x + view_w <= radar_x + radar_w:
        pygame.draw.rect(surface, (40, 70, 90), (cam_radar_x, radar_y + 1, view_w, radar_h - 2), 1)
    else:
        right_part = (radar_x + radar_w) - cam_radar_x
        left_part = view_w - right_part
        pygame.draw.rect(surface, (40, 70, 90), (cam_radar_x, radar_y + 1, right_part, radar_h - 2), 1)
        pygame.draw.rect(surface, (40, 70, 90), (radar_x, radar_y + 1, left_part, radar_h - 2), 1)

    def to_radar(wx: float, wy: float) -> tuple[int, int]:
        rx = radar_x + (wx / WORLD_WIDTH) * radar_w
        ry = radar_y + ((wy - radar_height) / (SCREEN_HEIGHT - radar_height)) * radar_h
        return int(rx), int(ry)

    for b in beacons:
        bx, _ = to_radar(b.pos.x, b.pos.y)
        if b.alive:
            b_col = BEACON_WARN_COLOR if (b.under_attack and (ticks // 140) % 2 == 0) else BEACON_COLOR
            pygame.draw.rect(surface, b_col, (bx - 2, radar_y + radar_h - 5, 4, 4))
        else:
            pygame.draw.rect(surface, CRATER_COLOR, (bx - 1, radar_y + radar_h - 4, 3, 3))

    for laser in lasers:
        lx, ly = to_radar(laser.pos.x, laser.pos.y)
        pygame.draw.rect(surface, LASER_COLOR, (lx, ly, 2, 1))

    for enemy in enemies:
        ex, ey = to_radar(enemy.pos.x, enemy.pos.y)
        col = CHARGER_COLOR if enemy.is_charger else LANDER_COLOR
        pygame.draw.circle(surface, col, (ex, ey), 3)

    px, py = to_radar(player.pos.x, player.pos.y)
    pygame.draw.circle(surface, SHIP_COLOR, (px, py), 3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Aegis Horizon — Combat & Base Defense")
    clock = pygame.time.Clock()

    hud_font = pygame.font.SysFont("consolas", 18, bold=True)
    small_font = pygame.font.SysFont("consolas", 13)
    banner_font = pygame.font.SysFont("consolas", 34, bold=True)

    radar_height = 70

    def reset_game():
        backdrop = WorldBackdrop(radar_height)
        player = PlayerShip(WORLD_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)
        beacons = []
        for i in range(6):
            bx = (i * (WORLD_WIDTH / 6)) + 300
            by = backdrop.get_terrain_y(bx)
            beacons.append(GroundBeacon(bx, by))

        return {
            "backdrop": backdrop,
            "player": player,
            "camera_x": player.pos.x,
            "beacons": beacons,
            "lasers": [],
            "enemies": [],
            "rings": [],
            "score": 0,
            "lives": 3,
            "elapsed_ms": 0,
            "last_spawn_ms": 0,
            "banner_text": "",
            "banner_color": SHIP_COLOR,
            "reset_at_ms": 0,
        }

    game = reset_game()

    running = True
    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Manual quick-reset key
                    game = reset_game()
                else:
                    game["player"].handle_keydown(event.key, now)

        # Auto-reset if round ended (all bases lost, 0 ships, or 3:00 survived)
        if game["reset_at_ms"] > 0:
            if now >= game["reset_at_ms"]:
                game = reset_game()
        else:
            game["elapsed_ms"] += dt
            remaining_sec = max(0.0, ROUND_DURATION_SEC - (game["elapsed_ms"] / 1000.0))
            progress = min(1.0, game["elapsed_ms"] / (ROUND_DURATION_SEC * 1000.0))

            # Escalating spawn rate & dive speed over the 3-minute timer
            spawn_interval_ms = max(950, int(2600 - 1650 * progress))
            speed_mult = 1.0 + 0.55 * progress

            if game["elapsed_ms"] - game["last_spawn_ms"] >= spawn_interval_ms:
                game["last_spawn_ms"] = game["elapsed_ms"]
                is_charger = (progress > 0.33) and (random.random() < 0.35)
                game["enemies"].append(
                    LanderEnemy(radar_height, game["beacons"], speed_mult, is_charger=is_charger)
                )

            keys = pygame.key.get_pressed()
            player: PlayerShip = game["player"]
            player.update(keys, top_bound=radar_height + 20, bottom_bound=SCREEN_HEIGHT - 45, now=now)

            if keys[pygame.K_SPACE]:
                bolt = player.try_fire(now)
                if bolt:
                    game["lasers"].append(bolt)

            for b in game["beacons"]:
                b.under_attack = False

            for laser in game["lasers"]:
                laser.update()

            for enemy in game["enemies"]:
                enemy.update(game["beacons"])
                if enemy.destroyed_beacon:
                    game["rings"].append(ImpactRing(enemy.pos.x, enemy.pos.y, BEACON_WARN_COLOR, max_radius=55))

            # Laser -> Enemy collisions
            for laser in game["lasers"]:
                if not laser.alive:
                    continue
                for enemy in game["enemies"]:
                    if not enemy.alive:
                        continue
                    dx = abs(wrap_delta(laser.pos.x, enemy.pos.x))
                    dy = abs(laser.pos.y - enemy.pos.y)
                    if dx <= enemy.radius + (laser.length * 0.5) and dy <= enemy.radius + 4:
                        laser.alive = False
                        enemy.alive = False
                        game["score"] += enemy.points_value
                        ring_col = CHARGER_COLOR if enemy.is_charger else LANDER_COLOR
                        game["rings"].append(ImpactRing(enemy.pos.x, enemy.pos.y, ring_col, max_radius=36))
                        break

            # Enemy -> Player collisions (ignored while boosting)
            if now >= player.invuln_until and not player.is_boosting(now):
                for enemy in game["enemies"]:
                    if not enemy.alive:
                        continue
                    dx = abs(wrap_delta(player.pos.x, enemy.pos.x))
                    dy = abs(player.pos.y - enemy.pos.y)
                    if dx <= enemy.radius + 14 and dy <= enemy.radius + 8:
                        enemy.alive = False
                        game["lives"] -= 1
                        player.invuln_until = now + 1800
                        game["rings"].append(ImpactRing(player.pos.x, player.pos.y, SHIP_COLOR, max_radius=45))
                        break

            for ring in game["rings"]:
                ring.update()

            game["lasers"] = [l for l in game["lasers"] if l.alive]
            game["enemies"] = [e for e in game["enemies"] if e.alive]
            game["rings"] = [r for r in game["rings"] if r.alive]

            # Smooth camera look-ahead
            look_ahead = (210 if player.is_boosting(now) else 160) * player.facing
            target_cam = (player.pos.x + look_ahead) % WORLD_WIDTH
            cam_diff = wrap_delta(target_cam, game["camera_x"])
            game["camera_x"] = (game["camera_x"] + cam_diff * 0.08) % WORLD_WIDTH

            # Check round end
            alive_beacons = sum(1 for b in game["beacons"] if b.alive)
            if alive_beacons == 0:
                game["banner_text"] = "ALL BASES LOST — REDEPLOYING..."
                game["banner_color"] = LANDER_COLOR
                game["reset_at_ms"] = now + 1800
            elif game["lives"] <= 0:
                game["banner_text"] = "SHIP DESTROYED — REDEPLOYING..."
                game["banner_color"] = LANDER_COLOR
                game["reset_at_ms"] = now + 1800
            elif remaining_sec <= 0.0:
                game["score"] += alive_beacons * 500
                game["banner_text"] = f"HORIZON SECURED! SCORE: {game['score']:05d}"
                game["banner_color"] = BEACON_COLOR
                game["reset_at_ms"] = now + 2200

        # --- Render ---
        screen.fill(BG_COLOR)
        cam_x = game["camera_x"]
        game["backdrop"].draw(screen, cam_x)

        for b in game["beacons"]:
            b.draw(screen, cam_x, now)
        for enemy in game["enemies"]:
            enemy.draw(screen, cam_x)
        for laser in game["lasers"]:
            laser.draw(screen, cam_x)
        for ring in game["rings"]:
            ring.draw(screen, cam_x)
        game["player"].draw(screen, cam_x, now)

        draw_scanner_hud(
            screen,
            game["player"],
            game["beacons"],
            game["enemies"],
            game["lasers"],
            cam_x,
            radar_height,
            now,
        )

        # HUD Text
        remaining_sec = max(0.0, ROUND_DURATION_SEC - (game["elapsed_ms"] / 1000.0))
        mins = int(remaining_sec) // 60
        secs = int(remaining_sec) % 60
        alive_beacons = sum(1 for b in game["beacons"] if b.alive)

        player = game["player"]
        boost_ready = now >= player.next_boost_allowed
        boost_text = "BOOST: ACTIVE" if player.is_boosting(now) else ("BOOST: READY (2x A/D)" if boost_ready else "BOOST: CHARGING")
        boost_col = BOOST_FLAME_COLOR if player.is_boosting(now) else (SHIP_COLOR if boost_ready else (110, 130, 140))

        score_surf = hud_font.render(f"SCORE: {game['score']:05d}", True, (220, 240, 245))
        ships_surf = small_font.render(f"SHIPS: {'▲ ' * max(0, game['lives'])}", True, SHIP_COLOR)
        boost_surf = small_font.render(boost_text, True, boost_col)
        screen.blit(score_surf, (16, 10))
        screen.blit(ships_surf, (16, 32))
        screen.blit(boost_surf, (16, 48))

        timer_color = (255, 80, 90) if remaining_sec <= 30 else (240, 245, 255)
        timer_surf = hud_font.render(f"TIME: {mins:02d}:{secs:02d}", True, timer_color)
        beacon_surf = small_font.render(f"BEACONS: {alive_beacons}/6", True, BEACON_COLOR)
        screen.blit(timer_surf, (SCREEN_WIDTH - timer_surf.get_width() - 16, 14))
        screen.blit(beacon_surf, (SCREEN_WIDTH - beacon_surf.get_width() - 16, 40))

        if game["banner_text"]:
            banner_surf = banner_font.render(game["banner_text"], True, game["banner_color"])
            screen.blit(banner_surf, (SCREEN_WIDTH // 2 - banner_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()