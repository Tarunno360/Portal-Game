from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

player_pos = [10.0, 0.0, 10.0]
player_yaw = 0.0
player_pitch = 0.0
cam_speed = 0.5
yaw_speed = 2.0
room_size = 20.0
wall_tiles = []
bullets = []
BULLET_SPEED = 7.0
BULLET_LIFETIME = 5.0
BULLET_RADIUS = 0.1
blue_shot_fired = False
yellow_shot_fired = False
last_teleport_time = 0.0
TELEPORT_COOLDOWN = 1.0
mouse_captured = False
window_width = 800
window_height = 600
v_y = 0.0
GRAVITY = -20.0
is_falling = False
BUTTON_POS = [2, 0, 2]
BUTTON_RADIUS = 2
BUTTON_HEIGHT = 0.833
door_color = 'red'
button_activated = False
game_won = False

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

def draw_bullet(bullet):
    glPushMatrix()
    glTranslatef(bullet.pos[0], bullet.pos[1], bullet.pos[2])
    if bullet.color == 'blue':
        glColor3f(0.0, 0.0, 1.0)
    else:
        glColor3f(1.0, 1.0, 0.0)
    glutSolidSphere(BULLET_RADIUS, 16, 16)
    glPopMatrix()

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

def draw_button():
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
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 0.0, 0.0, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(0.0, 0.0, 8.5)
    glVertex3f(4.0, 0.0, 8.5)
    glVertex3f(4.0, 9.0, 8.5)
    glVertex3f(0.0, 9.0, 8.5)
    glVertex3f(5.0, 0.0, 8.5)
    glVertex3f(9.0, 0.0, 8.5)
    glVertex3f(9.0, 9.0, 8.5)
    glVertex3f(5.0, 9.0, 8.5)
    glVertex3f(4.0, 0.0, 8.5)
    glVertex3f(5.0, 0.0, 8.5)
    glVertex3f(5.0, 2.0, 8.5)
    glVertex3f(4.0, 2.0, 8.5)
    glVertex3f(4.0, 3.0, 8.5)
    glVertex3f(5.0, 3.0, 8.5)
    glVertex3f(5.0, 9.0, 8.5)
    glVertex3f(4.0, 9.0, 8.5)
    glVertex3f(9.0, 0.0, 0.0)
    glVertex3f(9.0, 0.0, 8.5)
    glVertex3f(9.0, 9.0, 8.5)
    glVertex3f(9.0, 9.0, 0.0)
    glEnd()
    glDisable(GL_BLEND)

def draw_laser_door():
    if button_activated:
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

def draw_tile_with_door_color(tile):
    coords, color = tile
    x_min = min(v[0] for v in coords)
    x_max = max(v[0] for v in coords)
    y_min = min(v[1] for v in coords)
    z_min = min(v[2] for v in coords)
    is_door_tile = (abs(z_min - room_size) < 0.1 and
                    y_min < 6.0 and
                    6.67 - 0.1 <= x_min <= 13.33 + 0.1)
    if is_door_tile:
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
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glColor3f(1.0, 1.0, 1.0)
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

class Bullet:
    def __init__(self, pos, direction, color):
        self.pos = list(pos)
        self.velocity = [d * BULLET_SPEED for d in direction]
        self.time_alive = 0.0
        self.color = color
def update_bullets(dt):
    global bullets, wall_tiles, blue_shot_fired, yellow_shot_fired, button_activated
    if game_won:
        return
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
        if not button_activated:
            t = ray_plane_intersection(old_pos, new_pos, [0.0, 0.0, 15.0], [0.0, 0.0, 1.0])
            if t is not None:
                hit_point = [old_pos[i] + t * (new_pos[i] - old_pos[i]) for i in range(3)]
                if (0.0 <= hit_point[0] <= 20.0 and 0.0 <= hit_point[1] <= 9.0):
                    bullet_alive = False
                    continue
        t = ray_plane_intersection(old_pos, new_pos, [0.0, 0.0, 8.5], [0.0, 0.0, 1.0])
        if t is not None:
            hit_point = [old_pos[i] + t * (new_pos[i] - old_pos[i]) for i in range(3)]
            if (0.0 <= hit_point[0] <= 9.0 and 0.0 <= hit_point[1] <= 9.0):
                if not (4.0 <= hit_point[0] <= 5.0 and 2.0 <= hit_point[1] <= 3.0):
                    bullet_alive = False
                    continue
        t = ray_plane_intersection(old_pos, new_pos, [9.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        if t is not None:
            hit_point = [old_pos[i] + t * (new_pos[i] - old_pos[i]) for i in range(3)]
            if (0.0 <= hit_point[2] <= 8.5 and 0.0 <= hit_point[1] <= 9.0):
                bullet_alive = False
                continue
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

def reset_bullets():
    global bullets, blue_shot_fired, yellow_shot_fired, wall_tiles
    bullets = []
    blue_shot_fired = False
    yellow_shot_fired = False
    for tile in wall_tiles:
        tile[1] = 'gray'

def ray_aabb_intersection(start, end, aabb_min, aabb_max):
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
    direction = [end[i] - start[i] for i in range(3)]
    denom = sum(plane_normal[i] * direction[i] for i in range(3))
    if abs(denom) < 1e-6:
        return None
    t = sum(plane_normal[i] * (plane_point[i] - start[i]) for i in range(3)) / denom
    if t < 0 or t > 1:
        return None
    return t

def update_player_physics(dt):
    global player_pos, v_y, is_falling
    if game_won:
        return
    if is_falling and player_pos[1] > 0.0:
        v_y += GRAVITY * dt
        player_pos[1] += v_y * dt
        if player_pos[1] <= 0.0:
            player_pos[1] = 0.0
            v_y = 0.0
            is_falling = False

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

def check_player_tile_collision():
    global player_pos, wall_tiles, last_teleport_time, player_yaw, v_y, is_falling
    if game_won:
        return
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
            dest_color = 'yellow' if color == 'blue' else 'blue'
            for dest_tile in wall_tiles:
                dest_coords, dest_tile_color = dest_tile
                if dest_tile_color == dest_color:
                    dest_x = (min(v[0] for v in dest_coords) + max(v[0] for v in dest_coords)) / 2
                    dest_y = min(v[1] for v in dest_coords)
                    dest_z = (min(v[2] for v in dest_coords) + max(v[2] for v in dest_coords)) / 2
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
                    break
            break

def check_button_laser_collision():
    global player_pos
    if game_won:
        return
    if not (0.0 - 0.5 <= player_pos[1] <= 9.0 + 0.5):
        return
    if (0.0 <= player_pos[0] <= 9.0 and 8.0 <= player_pos[2] <= 9.0):
        reset_game()
        return
    if (8.5 <= player_pos[0] <= 9.5 and 0.0 <= player_pos[2] <= 8.5):
        reset_game()
        return

def check_door_collision():
    global player_pos, button_activated, game_won
    if game_won:
        return
    if (0.0 - 0.5 <= player_pos[0] <= 20.0 + 0.5 and
        0.0 - 0.5 <= player_pos[1] <= 9.0 + 0.5 and
        14.5 <= player_pos[2] <= 15.5):
        if not button_activated:
            reset_game()
        else:
            pass
    elif (6.67 - 0.5 <= player_pos[0] <= 13.33 + 0.5 and
          0.0 - 0.5 <= player_pos[1] <= 6.0 + 0.5 and
          19.9 <= player_pos[2] <= 20.1):
        if button_activated:
            game_won = True
        else:
            pass
        
def check_button_interaction():
    global door_color, button_activated
    if game_won:
        return
    if button_activated:
        return
    dx = player_pos[0] - BUTTON_POS[0]
    dz = player_pos[2] - BUTTON_POS[2]
    distance = math.sqrt(dx**2 + dz**2)
    if distance <= BUTTON_RADIUS and player_pos[1] <= BUTTON_HEIGHT + 0.1:
        door_color = 'green'
        button_activated = True

def mouse(button, state, x, y):
    global bullets, blue_shot_fired, yellow_shot_fired, mouse_captured
    if game_won:
        return
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
    glutPostRedisplay()

def mouse_motion(x, y):
    global player_yaw, player_pitch, mouse_captured
    if game_won:
        return
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

def keyboard(key, x, y):
    global player_pos, player_yaw, player_pitch, bullets, wall_tiles, blue_shot_fired, yellow_shot_fired, mouse_captured
    if game_won:
        return
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

def special_keys(key, x, y):
    global player_yaw
    if game_won:
        return
    if key == GLUT_KEY_LEFT:
        player_yaw -= yaw_speed
    elif key == GLUT_KEY_RIGHT:
        player_yaw += yaw_speed
    glutPostRedisplay()

def boundary_player_position():
    min_x, max_x = 0.1, 19.9
    min_z, max_z = 0.1, 19.9
    player_pos[0] = max(min_x, min(max_x, player_pos[0]))
    player_pos[2] = max(min_z, min(max_z, player_pos[2]))

def reset_game():
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

def reshape(w, h):
    global window_width, window_height
    window_width = w
    window_height = h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, w / float(h), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    if not game_won:
        check_player_tile_collision()
        check_door_collision()
        check_button_laser_collision()
        check_button_interaction()
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
