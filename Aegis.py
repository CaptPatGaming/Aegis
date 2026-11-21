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
TERRAIN_GLOW = (15, 70, 45)
HUD_BG = (15, 18, 30)
HUD_BORDER = (0, 180, 160)

def wrap_delta(target_x: float, camera_x: float) -> float:
    dx = (target_x - camera_x) % WORLD_WIDTH
    if dx > WORLD_WIDTH / 2:
        dx -= WORLD_WIDTH
    return dx

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

            if keys[pygame.K_a]:
                move_x -= 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                move_x = 1
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

            
                