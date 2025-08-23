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
JUMP_VELOCITY = 9.0  # Initial upward velocity for jump (~2.0 units high)
is_falling = False  # Tracks if player is falling or jumping

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

def update_bullets(dt):
    global bullets, wall_tiles, blue_shot_fired, yellow_shot_fired
    new_bullets = []
    blue_hit = False
    yellow_hit = False
    
    for bullet in bullets:
        bullet.time_alive += dt
        if bullet.time_alive < BULLET_LIFETIME:
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
    if is_falling or player_pos[1] > 0.0:
        v_y += GRAVITY * dt
        player_pos[1] += v_y * dt
        print(f"Vertical motion: y={player_pos[1]:.2f}, v_y={v_y:.2f}")
        if player_pos[1] <= 0.0:
            player_pos[1] = 0.0
            v_y = 0.0
            is_falling = False
            print("Landed on ground: y=0.0, v_y=0.0")

def check_player_tile_collision():
    global player_pos, wall_tiles, last_teleport_time, player_yaw, v_y, is_falling
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
    global player_pos, bullets, wall_tiles, blue_shot_fired, yellow_shot_fired, mouse_captured, v_y, is_falling
    key = key.decode("utf-8").lower()
    if key == '\x1b':
        mouse_captured = False
        glutSetCursor(GLUT_CURSOR_INHERIT)
    elif key == ' ' and player_pos[1] <= 0.01 and not is_falling:
        v_y = JUMP_VELOCITY
        is_falling = True
        print(f"Jump initiated: v_y={v_y:.2f}, y={player_pos[1]:.2f}")
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
            bullets = []
            blue_shot_fired = False
            yellow_shot_fired = False
            for tile in wall_tiles:
                tile[1] = 'gray'
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

def create_short_wall_with_tiles_with_door(start, end, height=9.0, rows=3, cols=12, door_rows=[0,1], door_col=6):
    x1, z1 = start
    x2, z2 = end
    length = math.sqrt((x2 - x1)**2 + (z2 - z1)**2)
    dx = (x2 - x1) / cols
    dz = (z2 - z1) / cols
    dy = height / rows
    for row in range(rows):
        for col in range(cols):
            if row in door_rows and col == door_col:
                continue
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
    # Draw base tile as gray
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

    # Draw filled oval portal for blue or yellow tiles
    if color in ['blue', 'yellow']:
        # Calculate tile center and normal
        x_min = min(v[0] for v in coords)
        x_max = max(v[0] for v in coords)
        y_min = min(v[1] for v in coords)
        y_max = max(v[1] for v in coords)
        z_min = min(v[2] for v in coords)
        z_max = max(v[2] for v in coords)
        center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]

        # Determine normal based on wall orientation
        normal = [0.0, 0.0, 0.0]
        if abs(z_max - z_min) < 0.1:  # Back (z=0) or front (z=20) wall
            normal[2] = 1.0 if z_min < 10.0 else -1.0
        elif abs(x_max - x_min) < 0.1:  # Left (x=0) or right (x=20) wall
            normal[0] = 1.0 if x_min < 10.0 else -1.0

        # Set portal color
        glColor3f(0.0, 0.0, 1.0) if color == 'blue' else glColor3f(1.0, 1.0, 0.0)

        # Draw filled oval
        glPushMatrix()
        # Translate to tile center, offset by normal
        glTranslatef(center[0] + normal[0] * 0.01, center[1] + normal[1] * 0.01, center[2] + normal[2] * 0.01)
        # Rotate to align with wall plane
        if normal[0] != 0.0:  # Left or right wall
            glRotatef(90.0, 0.0, 1.0, 0.0)
        # Scale to oval shape (width=1.34, height=2.4)
        glScalef(0.67, 1.2, 1.0)  # 0.67=1.34/2, 1.2=2.4/2
        segments = 32
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, 0.0)  # Center of the oval
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

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    check_player_tile_collision()
    print(f"Player position: {player_pos}, is_falling={is_falling}")
    lx = math.sin(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
    ly = math.sin(math.radians(player_pitch))
    lz = -math.cos(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
    gluLookAt(player_pos[0], player_pos[1] + 2.5, player_pos[2],
              player_pos[0] + lx, player_pos[1] + 2.5 + ly, player_pos[2] + lz,
              0, 1, 0)
    draw_floor_and_ceiling()
    for tile in wall_tiles:
        draw_tile(tile)
    for bullet in bullets:
        draw_bullet(bullet)
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    draw_gun_fps()
    glEnable(GL_DEPTH_TEST)
    draw_crosshair()
    glutSwapBuffers()

def boundary_player_position():
    min_x, max_x = 0.1, 19.9
    min_z, max_z = 0.1, 19.9
    player_pos[0] = max(min_x, min(max_x, player_pos[0]))
    player_pos[2] = max(min_z, min(max_z, player_pos[2]))

def special_keys(key, x, y):
    global player_yaw
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
    glClearColor(0.2, 0.2, 0.2, 1)
    wall_tiles.clear()
    create_wall_with_tiles((0, 0), (room_size, 0))  # Back wall
    create_wall_with_tiles((room_size, 0), (room_size, room_size))  # Right wall
    create_short_wall_with_tiles_with_door((room_size, room_size), (0, room_size))  # Front wall
    create_wall_with_tiles((0, room_size), (0, 0))  # Left wall
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
