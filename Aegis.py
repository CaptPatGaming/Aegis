import random
import pygame

# --- Configuration ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
WORLD_WIDTH = 3600  # 3.6x wider than the screen before wrapping
FPS = 60

# Colors (Vector-Neon Palette)
BG_COLOR = (8, 10, 18)
SHIP_COLOR = (0, 255, 220)
THRUST_COLOR = (255, 100, 50)
LASER_COLOR = (255, 240, 90)
ENEMY_COLOR = (255, 65, 105)
BEACON_COLOR = (60, 255, 150)
TERRAIN_COLOR = (40, 200, 120)
TERRAIN_GLOW = (15, 70, 45)
HUD_BG = (15, 18, 30)
HUD_BORDER = (0, 180, 160)


def wrap_delta(target_x: float, origin_x: float) -> float:
    """
    Calculates the shortest signed horizontal distance from origin_x to target_x
    across the circular world boundary [-WORLD_WIDTH/2, WORLD_WIDTH/2].
    """
    dx = (target_x - origin_x) % WORLD_WIDTH
    if dx > WORLD_WIDTH / 2:
        dx -= WORLD_WIDTH
    return dx


class GroundBeacon:
    """Stationary ground energy base anchored to the terrain ridge."""
    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.alive = True
        self.width = 26
        self.height = 24

    def draw(self, surface: pygame.Surface, camera_x: float):
        if not self.alive:
            return
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        if -50 <= screen_x <= SCREEN_WIDTH + 50:
            cx, by = int(screen_x), int(self.pos.y)
            # Pyramid base + floating energy core
            base_pts = [
                (cx - self.width // 2, by),
                (cx + self.width // 2, by),
                (cx + 6, by - self.height),
                (cx - 6, by - self.height),
            ]
            pygame.draw.polygon(surface, BEACON_COLOR, base_pts, width=2)
            pygame.draw.circle(surface, (220, 255, 240), (cx, by - self.height - 7), 4)


class LaserBolt:
    def __init__(self, x: float, y: float, facing: int):
        self.pos = pygame.math.Vector2(x, y)
        self.facing = facing
        self.speed = 22.0
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


class TargetDrone:
    """Patrolling target entity for combat & radar testing."""
    def __init__(self, radar_height: int):
        self.pos = pygame.math.Vector2(
            random.uniform(0, WORLD_WIDTH),
            random.uniform(radar_height + 45, SCREEN_HEIGHT - 160),
        )
        self.vel = pygame.math.Vector2(random.choice([-1.8, 1.8]), random.uniform(-0.8, 0.8))
        self.radius = 15
        self.alive = True
        self.radar_height = radar_height

    def update(self):
        self.pos.x = (self.pos.x + self.vel.x) % WORLD_WIDTH
        self.pos.y += self.vel.y

        if self.pos.y < self.radar_height + 35 or self.pos.y > SCREEN_HEIGHT - 150:
            self.vel.y *= -1

    def draw(self, surface: pygame.Surface, camera_x: float):
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        if -40 <= screen_x <= SCREEN_WIDTH + 40:
            cx, cy = int(screen_x), int(self.pos.y)
            r = self.radius
            points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(surface, ENEMY_COLOR, points, width=2)
            pygame.draw.circle(surface, (255, 180, 200), (cx, cy), 3)


class PlayerShip:
    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.facing = 1
        self.accel = 0.65
        self.friction = 0.92
        self.max_speed = 9.0
        self.width = 36
        self.height = 16
        self.fire_cooldown = 140
        self.last_shot_time = 0

    def update(self, keys: pygame.key.ScancodeWrapper, top_bound: int, bottom_bound: int):
        move_x = (1 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0) - (
            1 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0
        )
        move_y = (1 if (keys[pygame.K_DOWN] or keys[pygame.K_s]) else 0) - (
            1 if (keys[pygame.K_UP] or keys[pygame.K_w]) else 0
        )

        if move_x != 0:
            self.facing = move_x

        self.vel.x = (self.vel.x + move_x * self.accel) * self.friction
        self.vel.y = (self.vel.y + move_y * self.accel) * self.friction

        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

        self.pos.x = (self.pos.x + self.vel.x) % WORLD_WIDTH
        self.pos.y = max(top_bound, min(bottom_bound, self.pos.y + self.vel.y))

    def try_fire(self, current_time: int) -> LaserBolt | None:
        if current_time - self.last_shot_time >= self.fire_cooldown:
            self.last_shot_time = current_time
            nose_x = (self.pos.x + (self.width / 2) * self.facing) % WORLD_WIDTH
            return LaserBolt(nose_x, self.pos.y, self.facing)
        return None

    def draw(self, surface: pygame.Surface, camera_x: float):
        screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
        screen_y = self.pos.y

        nose = (screen_x + (self.width / 2) * self.facing, screen_y)
        top_wing = (screen_x - (self.width / 2) * self.facing, screen_y - self.height / 2)
        bottom_wing = (screen_x - (self.width / 2) * self.facing, screen_y + self.height / 2)
        notch = (screen_x - (self.width / 4) * self.facing, screen_y)

        if self.vel.length() > 1.5:
            flame_len = random.uniform(10, 22)
            flame_tip = (screen_x - (self.width / 2 + flame_len) * self.facing, screen_y)
            pygame.draw.polygon(surface, THRUST_COLOR, [top_wing, notch, bottom_wing, flame_tip])

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
        """Finds interpolated terrain height at world_x so beacons sit cleanly on the ridge."""
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


def check_laser_hits(lasers: list[LaserBolt], enemies: list[TargetDrone]) -> int:
    hits = 0
    for laser in lasers:
        if not laser.alive:
            continue
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = abs(wrap_delta(laser.pos.x, enemy.pos.x))
            dy = abs(laser.pos.y - enemy.pos.y)
            if dx <= enemy.radius + (laser.length * 0.5) and dy <= enemy.radius + 4:
                laser.alive = False
                enemy.alive = False
                hits += 1
                break
    return hits


def draw_scanner_hud(
    surface: pygame.Surface,
    player: PlayerShip,
    beacons: list[GroundBeacon],
    enemies: list[TargetDrone],
    lasers: list[LaserBolt],
    camera_x: float,
    radar_height: int,
):
    pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_WIDTH, radar_height))
    pygame.draw.line(surface, HUD_BORDER, (0, radar_height), (SCREEN_WIDTH, radar_height), 2)

    radar_w = 500
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

    # Ground beacons along the bottom of the radar
    for b in beacons:
        if b.alive:
            bx, _ = to_radar(b.pos.x, b.pos.y)
            pygame.draw.rect(surface, BEACON_COLOR, (bx - 2, radar_y + radar_h - 5, 4, 4))

    for laser in lasers:
        lx, ly = to_radar(laser.pos.x, laser.pos.y)
        pygame.draw.rect(surface, LASER_COLOR, (lx, ly, 2, 1))

    for enemy in enemies:
        ex, ey = to_radar(enemy.pos.x, enemy.pos.y)
        pygame.draw.circle(surface, ENEMY_COLOR, (ex, ey), 3)

    px, py = to_radar(player.pos.x, player.pos.y)
    pygame.draw.circle(surface, SHIP_COLOR, (px, py), 3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Aegis Horizon — Beacons Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)

    radar_height = 70
    player = PlayerShip(WORLD_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)
    backdrop = WorldBackdrop(radar_height)
    camera_x = player.pos.x

    # Place 6 ground energy beacons evenly across the 3600px wraparound world
    beacons: list[GroundBeacon] = []
    for i in range(6):
        bx = (i * (WORLD_WIDTH / 6)) + 300
        by = backdrop.get_terrain_y(bx)
        beacons.append(GroundBeacon(bx, by))

    lasers: list[LaserBolt] = []
    enemies: list[TargetDrone] = [TargetDrone(radar_height) for _ in range(10)]
    destroyed_count = 0

    running = True
    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.update(keys, top_bound=radar_height + 20, bottom_bound=SCREEN_HEIGHT - 45)

        if keys[pygame.K_SPACE]:
            bolt = player.try_fire(now)
            if bolt:
                lasers.append(bolt)

        for laser in lasers:
            laser.update()
        for enemy in enemies:
            enemy.update()

        destroyed_count += check_laser_hits(lasers, enemies)
        lasers = [l for l in lasers if l.alive]
        enemies = [e for e in enemies if e.alive]

        if not enemies:
            enemies = [TargetDrone(radar_height) for _ in range(10)]

        look_ahead_offset = 160 * player.facing
        target_cam_x = (player.pos.x + look_ahead_offset) % WORLD_WIDTH
        cam_diff = wrap_delta(target_cam_x, camera_x)
        camera_x = (camera_x + cam_diff * 0.08) % WORLD_WIDTH

        # --- Render ---
        screen.fill(BG_COLOR)
        backdrop.draw(screen, camera_x)
        for b in beacons:
            b.draw(screen, camera_x)
        for enemy in enemies:
            enemy.draw(screen, camera_x)
        for laser in lasers:
            laser.draw(screen, camera_x)
        player.draw(screen, camera_x)

        draw_scanner_hud(screen, player, beacons, enemies, lasers, camera_x, radar_height)

        alive_beacons = sum(1 for b in beacons if b.alive)
        left_hud = font.render(f"TARGETS HIT: {destroyed_count}", True, (220, 240, 245))
        right_hud = font.render(f"BEACONS: {alive_beacons}/6", True, BEACON_COLOR)
        screen.blit(left_hud, (16, 26))
        screen.blit(right_hud, (SCREEN_WIDTH - right_hud.get_width() - 16, 26))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()