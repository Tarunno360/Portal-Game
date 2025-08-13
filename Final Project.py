from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# Camera/player settings
player_pos = [10.0, 0.0, 10.0]  # Player position (center of room, ground level)
player_yaw = 0.0               # Player rotation (left/right)
player_pitch = 0.0             # Player rotation (up/down)
cam_speed = 0.5
yaw_speed = 2.0
room_size = 20.0
# Wall tile data
wall_tiles = []
# Bullet settings
bullets = []  # Stores active bullets
BULLET_SPEED = 7.0
BULLET_LIFETIME = 5.0
BULLET_RADIUS = 0.1
blue_shot_fired = False  # Tracks if any blue bullet hit a tile
yellow_shot_fired = False  # Tracks if any yellow bullet hit a tile
# Teleportation cooldown
last_teleport_time = 0.0
TELEPORT_COOLDOWN = 1.0  # Seconds
# Mouse capture settings
mouse_captured = False
window_width = 800
window_height = 600
# Physics settings
v_y = 0.0  # Vertical velocity
GRAVITY = -20.0  # Gravity acceleration
is_falling = False  # Tracks if player is falling after teleport
# Button settings
BUTTON_POS = [2, 0, 2]  # Button at (2, 0, 2), lower circular face on floor
BUTTON_RADIUS = 2  # Radius of cylinder
BUTTON_HEIGHT = 0.833  # Height of cylinder (1/3 player height)
door_color = 'red'  # Default door color
button_activated = False  # Tracks if button has been stepped on
# Win state
game_won = False  # Tracks if player has cleared the level

class Bullet:
    def __init__(self, pos, direction, color):
        self.pos = list(pos)  # [x, y, z]
        self.velocity = [d * BULLET_SPEED for d in direction]  # Scaled direction
        self.time_alive = 0.0
        self.color = color  # 'blue' or 'yellow'

def ray_aabb_intersection(start, end, aabb_min, aabb_max):
    """Check if a ray from start to end intersects an AABB."""
    tmin = 0.0
    tmax = 1.0
    direction = [end[i] - start[i] for i in range(3)]
    
    for i in range(3):
        if abs(direction[i]) < 1e-6:
            if start[i] < aabb_min[i] or start[i] > aabb_max[i]:
                return False
        else:
            ood = 1.0 / direction[i]
            t1 = (aabb_min[i] - start[i]) * ood
            t2 = (aabb_max[i] - start[i]) * ood
            tmin = max(tmin, min(t1, t2))
            tmax = min(tmax, max(t1, t2))
            if tmin > tmax:
                return False
    return tmin <= tmax and tmin <= 1.0

def ray_plane_intersection(start, end, plane_point, plane_normal):
    """Compute ray (start to end) intersection with a plane (point, normal). Returns t or None."""
    direction = [end[i] - start[i] for i in range(3)]
    denom = sum(plane_normal[i] * direction[i] for i in range(3))
    if abs(denom) < 1e-6:
        return None  # Ray parallel to plane
    t = sum(plane_normal[i] * (plane_point[i] - start[i]) for i in range(3)) / denom
    if t < 0 or t > 1:
        return None  # Intersection outside segment
    return t

def update_bullets(dt):
    global bullets, wall_tiles, blue_shot_fired, yellow_shot_fired, button_activated
    if game_won:
        return  # Skip bullet updates if game is won
    new_bullets = []
    blue_hit = False
    yellow_hit = False
    
    for bullet in bullets:
        bullet.time_alive += dt
        if bullet.time_alive >= BULLET_LIFETIME:
            continue
        old_pos = list(bullet.pos)
        bullet.pos[0] += bullet.velocity[0] * dt
        bullet.pos[1] += bullet.velocity[1] * dt
        bullet.pos[2] += bullet.velocity[2] * dt
        new_pos = bullet.pos
        if not (0 <= bullet.pos[0] <= room_size and 0 <= bullet.pos[2] <= room_size and
                0 <= bullet.pos[1] <= 9.0):
            new_bullets.append(bullet)
            continue
        bullet_alive = True

        # Check collision with door laser wall (Z=15, X=0-20, Y=0-9)
        if not button_activated:
            t = ray_plane_intersection(old_pos, new_pos, [0.0, 0.0, 15.0], [0.0, 0.0, 1.0])
            if t is not None:
                hit_point = [old_pos[i] + t * (new_pos[i] - old_pos[i]) for i in range(3)]
                if (0.0 <= hit_point[0] <= 20.0 and 0.0 <= hit_point[1] <= 9.0):
                    bullet_alive = False
                    print(f"{bullet.color} bullet hit door laser wall at {hit_point}")
                    continue

        # Check collision with button laser walls (Z=8.5, X=0-9; X=9, Z=0-8.5; Y=0-9)
        # Z=8.5 plane with hole at X=4-5, Y=2-3
        t = ray_plane_intersection(old_pos, new_pos, [0.0, 0.0, 8.5], [0.0, 0.0, 1.0])
        if t is not None:
            hit_point = [old_pos[i] + t * (new_pos[i] - old_pos[i]) for i in range(3)]
            if (0.0 <= hit_point[0] <= 9.0 and 0.0 <= hit_point[1] <= 9.0):
                if not (4.0 <= hit_point[0] <= 5.0 and 2.0 <= hit_point[1] <= 3.0):
                    bullet_alive = False
                    print(f"{bullet.color} bullet hit button laser wall at Z=8.5, point={hit_point}")
                    continue
        # X=9 plane (no hole)
        t = ray_plane_intersection(old_pos, new_pos, [9.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        if t is not None:
            hit_point = [old_pos[i] + t * (new_pos[i] - old_pos[i]) for i in range(3)]
            if (0.0 <= hit_point[2] <= 8.5 and 0.0 <= hit_point[1] <= 9.0):
                bullet_alive = False
                print(f"{bullet.color} bullet hit button laser wall at X=9, point={hit_point}")
                continue

        # Check collision with wall tiles
        for tile in wall_tiles:
            coords, _ = tile
            x_min = min(v[0] for v in coords)
            x_max = max(v[0] for v in coords)
            y_min = min(v[1] for v in coords)
            y_max = max(v[1] for v in coords)
            z_min = min(v[2] for v in coords)
            z_max = max(v[2] for v in coords)
            aabb_min = [x_min - BULLET_RADIUS, y_min - BULLET_RADIUS, z_min - BULLET_RADIUS]
            aabb_max = [x_max + BULLET_RADIUS, y_max + BULLET_RADIUS, z_max + BULLET_RADIUS]
            if ray_aabb_intersection(old_pos, new_pos, aabb_min, aabb_max):
                tile[1] = bullet.color
                bullet_alive = False
                if bullet.color == 'blue':
                    blue_hit = True
                else:
                    yellow_hit = True
                print(f"{bullet.color} bullet hit wall tile at {new_pos}")
                break

        if bullet_alive:
            new_bullets.append(bullet)

    if blue_hit:
        blue_shot_fired = True
        new_bullets = [b for b in new_bullets if b.color != 'blue']
    if yellow_hit:
        yellow_shot_fired = True
        new_bullets = [b for b in new_bullets if b.color != 'yellow']
    bullets = new_bullets

def update_player_physics(dt):
    global player_pos, v_y, is_falling
    if game_won:
        return  # Skip physics if game is won
    if is_falling and player_pos[1] > 0.0:
        v_y += GRAVITY * dt
        player_pos[1] += v_y * dt
        print(f"Falling: y={player_pos[1]:.2f}, v_y={v_y:.2f}")
        if player_pos[1] <= 0.0:
            player_pos[1] = 0.0
            v_y = 0.0
            is_falling = False
            print("Landed on ground: y=0.0, v_y=0.0")

def check_player_tile_collision():
    global player_pos, wall_tiles, last_teleport_time, player_yaw, v_y, is_falling
    if game_won:
        return  # Skip collision checks if game is won
    from time import time
    current_time = time()
    if current_time - last_teleport_time < TELEPORT_COOLDOWN:
        return
    teleported = False
    for tile in wall_tiles:
        coords, color = tile
        if color not in ['blue', 'yellow'] or teleported:
            continue
        x_min = min(v[0] for v in coords)
        x_max = max(v[0] for v in coords)
        y_min = min(v[1] for v in coords)
        y_max = max(v[1] for v in coords)
        z_min = min(v[2] for v in coords)
        z_max = max(v[2] for v in coords)
        if (x_min - 0.5 <= player_pos[0] <= x_max + 0.5 and
            y_min - 0.5 <= player_pos[1] <= y_max + 0.5 and
            z_min - 0.5 <= player_pos[2] <= z_max + 0.5):
            print(f"Player at {player_pos} touched {color} tile, searching for {'yellow' if color == 'blue' else 'blue'}")
            dest_color = 'yellow' if color == 'blue' else 'blue'
            for dest_tile in wall_tiles:
                dest_coords, dest_tile_color = dest_tile
                if dest_tile_color == dest_color:
                    dest_x = (min(v[0] for v in dest_coords) + max(v[0] for v in dest_coords)) / 2
                    dest_y = min(v[1] for v in dest_coords)
                    dest_z = (min(v[2] for v in dest_coords) + max(v[2] for v in dest_coords)) / 2
                    print(f"Dest tile: y_min={y_min:.2f}, y_max={y_max:.2f}, dest_y={dest_y:.2f}")
                    if abs(dest_x) < 0.1:
                        dest_x += 2.0
                        player_yaw = 90
                    elif abs(dest_x - room_size) < 0.1:
                        dest_x -= 2.0
                        player_yaw = -90
                    if abs(dest_z) < 0.1:
                        dest_z += 2.0
                        player_yaw = 180
                    elif abs(dest_z - room_size) < 0.1:
                        dest_z -= 2.0
                        player_yaw = 0
                    player_pos[0] = dest_x
                    player_pos[1] = dest_y
                    player_pos[2] = dest_z
                    v_y = 0.0
                    is_falling = True
                    boundary_player_position()
                    last_teleport_time = current_time
                    teleported = True
                    print(f"Teleported to {dest_color} tile at {player_pos} (y={dest_y:.2f}), cooldown started")
                    break
            break

def reset_game():
    """Reset the game to initial state."""
    global player_pos, player_yaw, player_pitch, bullets, blue_shot_fired, yellow_shot_fired
    global door_color, button_activated, v_y, is_falling, last_teleport_time, wall_tiles, game_won
    player_pos = [10.0, 0.0, 10.0]
    player_yaw = 0.0
    player_pitch = 0.0
    bullets = []
    blue_shot_fired = False
    yellow_shot_fired = False
    for tile in wall_tiles:
        tile[1] = 'gray'
    door_color = 'red'
    button_activated = False
    v_y = 0.0
    is_falling = False
    last_teleport_time = 0.0
    game_won = False
    print("Game reset: Player at [10.0, 0.0, 10.0], tiles gray, door red, button off, game_won=False")

def reset_bullets():
    """Reset bullet allowances and clear portals."""
    global bullets, blue_shot_fired, yellow_shot_fired, wall_tiles
    bullets = []
    blue_shot_fired = False
    yellow_shot_fired = False
    for tile in wall_tiles:
        tile[1] = 'gray'
    print("Bullets and portals reset: blue_shot_fired=False, yellow_shot_fired=False, tiles gray")

def check_button_laser_collision():
    """Check if player is too close to button laser walls, reset game if so."""
    global player_pos
    if game_won:
        return  # Skip collision checks if game is won
    if not (0.0 - 0.5 <= player_pos[1] <= 9.0 + 0.5):
        return
    if (0.0 <= player_pos[0] <= 9.0 and 8.0 <= player_pos[2] <= 9.0):
        print(f"Player at {player_pos} touched button laser wall at Z=8.5, resetting game")
        reset_game()
        return
    if (8.5 <= player_pos[0] <= 9.5 and 0.0 <= player_pos[2] <= 8.5):
        print(f"Player at {player_pos} touched button laser wall at X=9, resetting game")
        reset_game()
        return

def check_door_collision():
    """Check if player touches door laser wall or green door tiles, handle reset or win."""
    global player_pos, button_activated, game_won
    if game_won:
        return  # Skip collision checks if game is won
    # Check invisible laser wall at Z=15
    if (0.0 - 0.5 <= player_pos[0] <= 20.0 + 0.5 and
        0.0 - 0.5 <= player_pos[1] <= 9.0 + 0.5 and
        14.5 <= player_pos[2] <= 15.5):
        if not button_activated:
            print(f"Player at {player_pos} touched door laser wall at X=0-20, Y=0-9, Z=14.5-15.5, resetting game")
            reset_game()
        else:
            print(f"Player at {player_pos} passed through Z=14.5-15.5 (green door active), no action")
    # Check green door tiles at Z=20, X=6.67-13.33, Y=0-6
    elif (6.67 - 0.5 <= player_pos[0] <= 13.33 + 0.5 and
          0.0 - 0.5 <= player_pos[1] <= 6.0 + 0.5 and
          19.9 <= player_pos[2] <= 20.1):
        if button_activated:
            game_won = True
            print(f"Player cleared level at {player_pos}: Touched green door tiles, game_won=True")
        else:
            print(f"Player at {player_pos} touched door tiles at X=6.67-13.33, Y=0-6, Z=19.9-20.1, but door is red")
    else:
        print(f"Player at {player_pos}, not at laser wall (Z=14.5-15.5) or door tiles (Z=19.9-20.1), button_activated={button_activated}, game_won={game_won}")

def draw_bullet(bullet):
    glPushMatrix()
    glTranslatef(bullet.pos[0], bullet.pos[1], bullet.pos[2])
    if bullet.color == 'blue':
        glColor3f(0.0, 0.0, 1.0)
    else:
        glColor3f(1.0, 1.0, 0.0)
    glutSolidSphere(BULLET_RADIUS, 16, 16)
    glPopMatrix()

def mouse(button, state, x, y):
    global bullets, blue_shot_fired, yellow_shot_fired, mouse_captured
    if game_won:
        return  # Ignore mouse input if game is won
    if state == GLUT_DOWN:
        if button == GLUT_LEFT_BUTTON:
            if not mouse_captured:
                mouse_captured = True
                glutSetCursor(GLUT_CURSOR_NONE)
                glutWarpPointer(window_width // 2, window_height // 2)
            if not blue_shot_fired:
                lx = math.sin(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
                ly = math.sin(math.radians(player_pitch))
                lz = -math.cos(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
                direction = [lx, ly, lz]
                bullet_pos = [
                    player_pos[0] + lx * 0.8,
                    player_pos[1] + 2.5 + ly * 0.8,
                    player_pos[2] + lz * 0.8
                ]
                bullets.append(Bullet(bullet_pos, direction, 'blue'))
                print(f"Shot blue bullet at {bullet_pos}")
        elif button == GLUT_RIGHT_BUTTON and mouse_captured:
            if not yellow_shot_fired:
                lx = math.sin(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
                ly = math.sin(math.radians(player_pitch))
                lz = -math.cos(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
                direction = [lx, ly, lz]
                bullet_pos = [
                    player_pos[0] + lx * 0.8,
                    player_pos[1] + 2.5 + ly * 0.8,
                    player_pos[2] + lz * 0.8
                ]
                bullets.append(Bullet(bullet_pos, direction, 'yellow'))
                print(f"Shot yellow bullet at {bullet_pos}")
    glutPostRedisplay()

def keyboard(key, x, y):
    global player_pos, player_yaw, player_pitch, bullets, wall_tiles, blue_shot_fired, yellow_shot_fired, mouse_captured
    if game_won:
        return  # Ignore keyboard input if game is won
    key = key.decode("utf-8").lower()
    if key == '\x1b':
        mouse_captured = False
        glutSetCursor(GLUT_CURSOR_INHERIT)
    else:
        lx = math.sin(math.radians(player_yaw))
        lz = -math.cos(math.radians(player_yaw))
        if key == 'w':
            player_pos[0] += lx * cam_speed
            player_pos[2] += lz * cam_speed
        elif key == 's':
            player_pos[0] -= lx * cam_speed
            player_pos[2] -= lz * cam_speed
        elif key == 'a':
            player_pos[0] += lz * cam_speed
            player_pos[2] -= lx * cam_speed
        elif key == 'd':
            player_pos[0] -= lz * cam_speed
            player_pos[2] += lx * cam_speed
        elif key == 'r':
            reset_game()
        elif key == 'p':
            reset_bullets()
    boundary_player_position()
    glutPostRedisplay()

def timer(value):
    update_bullets(0.016)
    update_player_physics(0.016)
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def create_wall_with_tiles(start, end, height=9.0, rows=3, cols=12):
    x1, z1 = start
    x2, z2 = end
    length = math.sqrt((x2 - x1)**2 + (z2 - z1)**2)
    dx = (x2 - x1) / cols
    dz = (z2 - z1) / cols
    dy = height / rows
    for row in range(rows):
        for col in range(cols):
            y_bottom = row * dy
            y_top = (row + 1) * dy
            x_left = x1 + col * dx
            z_left = z1 + col * dz
            x_right = x1 + (col + 1) * dx
            z_right = z1 + (col + 1) * dz
            tile_coords = [
                (x_left, y_bottom, z_left),
                (x_right, y_bottom, z_right),
                (x_right, y_top, z_right),
                (x_left, y_top, z_left)
            ]
            wall_tiles.append([tile_coords, 'gray'])
            print(f"Wall tile: x=({x_left:.2f}, {x_right:.2f}), z=({z_left:.2f}, {z_right:.2f}), y=({y_bottom:.2f}, {y_top:.2f})")

def create_short_wall_with_tiles_with_door(start, end, height=9.0, rows=3, cols=12):
    x1, z1 = start
    x2, z2 = end
    length = math.sqrt((x2 - x1)**2 + (z2 - z1)**2)
    dx = (x2 - x1) / cols
    dz = (z2 - z1) / cols
    dy = height / rows
    for row in range(rows):
        for col in range(cols):
            y_bottom = row * dy
            y_top = (row + 1) * dy
            x_left = x1 + col * dx
            z_left = z1 + col * dz
            x_right = x1 + (col + 1) * dx
            z_right = z1 + (col + 1) * dz
            tile_coords = [
                (x_left, y_bottom, z_left),
                (x_right, y_bottom, z_right),
                (x_right, y_top, z_right),
                (x_left, y_top, z_left)
            ]
            wall_tiles.append([tile_coords, 'gray'])
            print(f"Front wall tile: x=({x_left:.2f}, {x_right:.2f}), z=({z_left:.2f}, {z_right:.2f}), y=({y_bottom:.2f}, {y_top:.2f})")

def draw_tile(tile):
    coords, color = tile
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(2.0, 2.0)
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    for vertex in coords:
        glVertex3fv(vertex)
    glEnd()
    glDisable(GL_POLYGON_OFFSET_FILL)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINE_LOOP)
    for vertex in coords:
        glVertex3fv(vertex)
    glEnd()

    if color in ['blue', 'yellow']:
        x_min = min(v[0] for v in coords)
        x_max = max(v[0] for v in coords)
        y_min = min(v[1] for v in coords)
        y_max = max(v[1] for v in coords)
        z_min = min(v[2] for v in coords)
        z_max = max(v[2] for v in coords)
        center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
        normal = [0.0, 0.0, 0.0]
        if abs(z_max - z_min) < 0.1:
            normal[2] = 1.0 if z_min < 10.0 else -1.0
        elif abs(x_max - x_min) < 0.1:
            normal[0] = 1.0 if x_min < 10.0 else -1.0
        glColor3f(0.0, 0.0, 1.0) if color == 'blue' else glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glTranslatef(center[0] + normal[0] * 0.01, center[1] + normal[1] * 0.01, center[2] + normal[2] * 0.01)
        if normal[0] != 0.0:
            glRotatef(90.0, 0.0, 1.0, 0.0)
        glScalef(0.67, 1.2, 1.0)
        segments = 32
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, 0.0)
        for i in range(segments + 1):
            theta = 2.0 * math.pi * i / segments
            glVertex3f(math.cos(theta), math.sin(theta), 0.0)
        glEnd()
        glPopMatrix()
        print(f"Drawing {color} portal at center={center}, normal={normal}")

def draw_floor_and_ceiling():
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(20, 0, 0)
    glVertex3f(20, 0, 20)
    glVertex3f(0, 0, 20)
    glEnd()
    glColor3f(0.75, 0.75, 0.75)
    glBegin(GL_QUADS)
    glVertex3f(0, 9.0, 0)
    glVertex3f(20, 9.0, 0)
    glVertex3f(20, 9.0, 20)
    glVertex3f(0, 9.0, 20)
    glEnd()

def draw_gun_fps():
    glPushMatrix()
    glTranslatef(0.2, -0.3, -0.8)
    glPushMatrix()
    glColor3f(0.15, 0.15, 0.15)
    gluCylinder(gluNewQuadric(), 0.07, 0.07, 0.2, 32, 8)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.1)
    glTranslatef(0.0, 0.0, 0.2)
    gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.6, 32, 8)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.12, 0.12, 0.12)
    glTranslatef(0.0, -0.15, 0.05)
    glRotatef(75, 1, 0, 0)
    glScalef(0.08, 0.3, 0.1)
    glutSolidCube(0.5)
    glPopMatrix()
    glPopMatrix()

def mouse_motion(x, y):
    global player_yaw, player_pitch, mouse_captured
    if game_won:
        return  # Ignore mouse motion if game is won
    if not mouse_captured:
        return
    center_x = window_width // 2
    center_y = window_height // 2
    dx = x - center_x
    dy = y - center_y
    sensitivity = 0.2
    player_yaw += dx * sensitivity
    player_pitch -= dy * sensitivity
    player_pitch = max(-89, min(89, player_pitch))
    glutWarpPointer(center_x, center_y)
    glutPostRedisplay()

def draw_crosshair():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1, 0, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glColor3f(0, 0, 0)
    cx, cy = 0.5, 0.5
    r_outer = 0.015
    r_dot = 0.002
    glBegin(GL_LINE_LOOP)
    for i in range(64):
        angle = 2.0 * math.pi * i / 64
        glVertex2f(cx + math.cos(angle) * r_outer, cy + math.sin(angle) * r_outer)
    glEnd()
    glBegin(GL_POLYGON)
    for i in range(32):
        angle = 2.0 * math.pi * i / 32
        glVertex2f(cx + math.cos(angle) * r_dot, cy + math.sin(angle) * r_dot)
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_button():
    """Draw a vertical cylindrical button at BUTTON_POS and transparent red laser walls with a hole."""
    glPushMatrix()
    glTranslatef(BUTTON_POS[0], BUTTON_POS[1], BUTTON_POS[2])
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.1, 0.2, 0.3)
    glEnable(GL_DEPTH_TEST)
    quad = gluNewQuadric()
    gluCylinder(quad, BUTTON_RADIUS, BUTTON_RADIUS, BUTTON_HEIGHT, 32, 8)
    gluDisk(quad, 0.0, BUTTON_RADIUS, 32, 8)
    glTranslatef(0.0, 0.0, BUTTON_HEIGHT)
    gluDisk(quad, 0.0, BUTTON_RADIUS, 32, 8)
    glPopMatrix()

    # Draw transparent red laser walls with hole at X=4-5, Y=2-3 on Z=8.5 wall
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 0.0, 0.0, 0.5)
    glBegin(GL_QUADS)
    # Z=8.5 wall, split around X=4-5, Y=2-3
    # Left part: X=0-4, Y=0-9
    glVertex3f(0.0, 0.0, 8.5)
    glVertex3f(4.0, 0.0, 8.5)
    glVertex3f(4.0, 9.0, 8.5)
    glVertex3f(0.0, 9.0, 8.5)
    # Right part: X=5-9, Y=0-9
    glVertex3f(5.0, 0.0, 8.5)
    glVertex3f(9.0, 0.0, 8.5)
    glVertex3f(9.0, 9.0, 8.5)
    glVertex3f(5.0, 9.0, 8.5)
    # Bottom part: X=4-5, Y=0-2
    glVertex3f(4.0, 0.0, 8.5)
    glVertex3f(5.0, 0.0, 8.5)
    glVertex3f(5.0, 2.0, 8.5)
    glVertex3f(4.0, 2.0, 8.5)
    # Top part: X=4-5, Y=3-9
    glVertex3f(4.0, 3.0, 8.5)
    glVertex3f(5.0, 3.0, 8.5)
    glVertex3f(5.0, 9.0, 8.5)
    glVertex3f(4.0, 9.0, 8.5)
    # X=9 wall (no hole)
    glVertex3f(9.0, 0.0, 0.0)
    glVertex3f(9.0, 0.0, 8.5)
    glVertex3f(9.0, 9.0, 8.5)
    glVertex3f(9.0, 9.0, 0.0)
    glEnd()
    glDisable(GL_BLEND)
    print(f"Drawing button at {BUTTON_POS}, height={BUTTON_HEIGHT}, radius={BUTTON_RADIUS}, transparent laser walls with hole at X=4-5, Y=2-3, Z=8.5")

def draw_laser_door():
    """Draw a transparent red laser wall across the front wall, unless door is green."""
    if button_activated:
        print("Door is green, skipping door laser wall draw")
        return
    glPushMatrix()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1, 0.0, 0, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(0.0, 0.0, 15.0)
    glVertex3f(20.0, 0.0, 15.0)
    glVertex3f(20.0, 9.0, 15.0)
    glVertex3f(0.0, 9.0, 15.0)
    glEnd()
    glDisable(GL_BLEND)
    glPopMatrix()
    print("Drawing transparent door laser wall at X=0-20, Y=0-9, Z=15.0")

def check_button_interaction():
    """Check if player steps on the button and set door color to green permanently."""
    global door_color, button_activated
    if game_won:
        return  # Skip button interaction if game is won
    if button_activated:
        return
    dx = player_pos[0] - BUTTON_POS[0]
    dz = player_pos[2] - BUTTON_POS[2]
    distance = math.sqrt(dx**2 + dz**2)
    if distance <= BUTTON_RADIUS and player_pos[1] <= BUTTON_HEIGHT + 0.1:
        door_color = 'green'
        button_activated = True
        print(f"Player at {player_pos} stepped on button: Door color set to green permanently, game_won={game_won}")
    else:
        print(f"Player at {player_pos}, button not activated yet, game_won={game_won}")

def draw_tile_with_door_color(tile):
    """Wrap draw_tile to apply door color to door tiles (cols 4-8, rows 0-1)."""
    coords, color = tile
    x_min = min(v[0] for v in coords)
    x_max = max(v[0] for v in coords)
    y_min = min(v[1] for v in coords)
    z_min = min(v[2] for v in coords)
    is_door_tile = (abs(z_min - room_size) < 0.1 and
                    y_min < 6.0 and
                    6.67 - 0.1 <= x_min <= 13.33 + 0.1)
    if is_door_tile:
        print(f"Door tile detected at x_min={x_min:.2f}, y_min={y_min:.2f}, z_min={z_min:.2f}, applying {door_color}")
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        glColor3f(0.0, 1.0, 0.0) if door_color == 'green' else glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        for vertex in coords:
            glVertex3fv(vertex)
        glEnd()
        glDisable(GL_POLYGON_OFFSET_FILL)
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINE_LOOP)
        for vertex in coords:
            glVertex3fv(vertex)
        glEnd()
    else:
        draw_tile(tile)

def draw_win_message():
    """Draw 'You Have Cleared This Level' in the center of the screen."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glColor3f(1.0, 1.0, 1.0)  # White text
    text = "You Have Cleared This Level"
    font = GLUT_BITMAP_HELVETICA_18
    text_width = sum(glutBitmapWidth(font, ord(c)) for c in text)
    x = (window_width - text_width) / 2
    y = window_height / 2
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    if not game_won:
        check_player_tile_collision()
        check_door_collision()
        check_button_laser_collision()
        check_button_interaction()
        print(f"Player position: {player_pos}, is_falling={is_falling}, door_color={door_color}, button_activated={button_activated}, game_won={game_won}")
        lx = math.sin(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
        ly = math.sin(math.radians(player_pitch))
        lz = -math.cos(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
        gluLookAt(player_pos[0], player_pos[1] + 2.5, player_pos[2],
                  player_pos[0] + lx, player_pos[1] + 2.5 + ly, player_pos[2] + lz,
                  0, 1, 0)
        draw_floor_and_ceiling()
        draw_button()
        draw_laser_door()
        for tile in wall_tiles:
            draw_tile_with_door_color(tile)
        for bullet in bullets:
            draw_bullet(bullet)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        draw_gun_fps()
        glEnable(GL_DEPTH_TEST)
        draw_crosshair()
    if game_won:
        draw_win_message()
    glutSwapBuffers()

def boundary_player_position():
    min_x, max_x = 0.1, 19.9
    min_z, max_z = 0.1, 19.9
    player_pos[0] = max(min_x, min(max_x, player_pos[0]))
    player_pos[2] = max(min_z, min(max_z, player_pos[2]))

def special_keys(key, x, y):
    global player_yaw
    if game_won:
        return  # Ignore special keys if game is won
    if key == GLUT_KEY_LEFT:
        player_yaw -= yaw_speed
    elif key == GLUT_KEY_RIGHT:
        player_yaw += yaw_speed
    glutPostRedisplay()

def reshape(w, h):
    global window_width, window_height
    window_width = w
    window_height = h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, w / float(h), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def init():
    global room_size, wall_tiles
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(0.2, 0.2, 0.2, 1)
    wall_tiles.clear()
    create_wall_with_tiles((0, 0), (room_size, 0))
    create_wall_with_tiles((room_size, 0), (room_size, room_size))
    create_short_wall_with_tiles_with_door((room_size, room_size), (0, room_size))
    create_wall_with_tiles((0, room_size), (0, 0))
    glutTimerFunc(0, timer, 0)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"Portal Game Demo")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutPassiveMotionFunc(mouse_motion)
    glutMouseFunc(mouse)
    glutMainLoop()

if __name__ == "__main__":
    main()
