import random 
import pygame

#Configuration
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
WORLD_WIDTH = 3600
FPS = 60

#Colours
BG_COLOR = (8, 10, 18)
SHIP_COLOR = (0, 255, 220)
THRUST_COLOR = (255, 100, 50)
TERRAIN_COLOR = (40)
TERRAIN_GLOW = (15, 70, 45)
HUD_BG = (15, 18, 30)
HUD_BORDER = (0, 180, 160)

# Wrap the world
def wrap_delta(target_x: float, camera_x: float) -> float:
    dx = (target_x - camera_x) % WORLD_WIDTH
    if dx > WORLD_WIDTH / 2:
        dx -= WORLD_WIDTH
    return dx


    # Program The ship
class playerShip:
    def __init__(self, x: float, y: float):
        self.pos = pygame.math.Vector2(x,y)
        self.vel = pygame.math.Vector2(0,0)
        self.facing = 1 
        self.accel = 0.65
        self.friction = 0.92
        self.max_speed = 9.0
        self.width = 36
        self.height = 16

        def update(self, keys: pygame.key.ScancodeWrapper, top_bound: int, bottom_bound: int):
            move_x = 0
            move_y = 0

            # Keybind code
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                move_x -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                move_x += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                move_y -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                move_y += 1

# Program Directional Autoface
            if move_x != 0: 
                self.facing = move_x

            #Friction code
            self.vel.x = (self.vel.x + move_x * self.accel) * self.friction
            self.vel.y = (self.vel.y + move_y * self.accel) * self.friction

            #Clamp Speed
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)
            #Update postion around W_WIDTH
            self.pos.x = (self.pos.x + self.vel.x) % WORLD_WIDTH
            self.pos.y = max(top_bound, min(bottom_bound, self.pos.y + self.vel.y))
                
        def draw(self, surface: pygame.Surface, camera_x: float):
            screen_x = SCREEN_WIDTH / 2 + wrap_delta(self.pos.x, camera_x)
            screen_y = self.pos.y
                
            # Vector ship vertices oriented to self.facing
            nose = (screen_x + (self.width / 2) * self.facing, screen_y)
            top_wing = (screen_x - (self.width / 2) * self.facing, screen_y - self.height / 2)
            bottom_wing = (screen_x - (self.width / 2) * self.facing, screen_y + self.height / 2 )
            notch = (screen_x - (self.width / 4) * self.facing, screen_y)
                
            # Draw thruster flame when moving fast
            if self.vel.length() > 1.5:
                flame_len = random.uniform(10, 22)
                flame_tip = (screen_x - (self.width / 2 + flame_len) * self.facing, screen_y)
                pygame.draw.polygon(surface, THRUST_COLOR, [top_wing, notch, bottom_wing, flame_tip])

        
        # Draw ship hull
                pygame.draw.polygon(surface, SHIP_COLOR, [nose, top_wing, notch, bottom_wing], width=2)


class worldBackdrop:
    def __init__(self, radar_height: int):
        self.radar_height = radar_height
        # Generate looping starfield (x, y, parallax_factor, brightness)
        self.stars = [
            (
                random.uniform(0, WORLD_WIDTH),
                random.uniform(radar_height + 10, SCREEN_HEIGHT - 120),
                random.choice([0.3, 0.6, 1.0]),
                random.randint(90, 220),
            )
            for _ in range(140)
        ]

        # Generate seamless procedural mountain peaks across WORLD_WIDTH
        self.segment_width = 75
        num_segments = WORLD_WIDTH // self.segment_width
        self.terrain_points = []
        for i in range(num_segments):
            x = i * self.segment_width
            y = SCREEN_HEIGHT - random.randint(45, 130)
            self.terrain_points.append((x, y))

    def draw(self, surface: pygame.Surface, camera_x: float):
        # 1. Draw Parallax Stars
        for star_x, star_y, parallax, brightness in self.stars:
            # Apply parallax relative to camera movement
            effective_cam = (camera_x * parallax) % WORLD_WIDTH
            sx = SCREEN_WIDTH / 2 + wrap_delta(star_x, effective_cam)
            if 0 <= sx <= SCREEN_WIDTH:
                color = (brightness, brightness, min(255, brightness + 30))
                size = 2 if parallax == 1.0 else 1
                pygame.draw.rect(surface, color, (sx, star_y, size, size))

        # 2. Draw Seamless Wrapping Vector Terrain
        visible_points = []
        for world_x, world_y in self.terrain_points:
            sx = SCREEN_WIDTH / 2 + wrap_delta(world_x, camera_x)
            # Only collect points near or inside the screen viewport
            if -self.segment_width * 2 <= sx <= SCREEN_WIDTH + self.segment_width * 2:
                visible_points.append((sx, world_y))

        # Sort left-to-right on screen so the line connects cleanly across the wrap seam
        visible_points.sort(key=lambda p: p[0])

        if len(visible_points) >= 2:
            # Subtle glow pass underneath
            glow_points = [(x, y + 3) for x, y in visible_points]
            pygame.draw.lines(surface, TERRAIN_GLOW, False, glow_points, width=5)
            # Sharp vector top ridge
            pygame.draw.lines(surface, TERRAIN_COLOR, False, visible_points, width=2)
