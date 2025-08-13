from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# Camera/player settings
player_pos = [10.0, 2.5, 6.0]  # Player position (center of room)
player_yaw = 0.0               # Player rotation (left/right)
player_pitch = 0.0             # Player rotation (up/down)
cam_speed = 0.5
yaw_speed = 2.0

# Wall tile data
wall_tiles = []

def create_wall_with_tiles(start, end, height=5.0, rows=2, cols=13):
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

            tile = [
                (x_left, y_bottom, z_left),
                (x_right, y_bottom, z_right),
                (x_right, y_top, z_right),
                (x_left, y_top, z_left)
            ]
            wall_tiles.append(tile)

def draw_tile(tile_coords):
    # Draw tile fill (light gray)
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0, 1.0)
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    for vertex in tile_coords:
        glVertex3fv(vertex)
    glEnd()
    glDisable(GL_POLYGON_OFFSET_FILL)

    # Draw border (black)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINE_LOOP)
    for vertex in tile_coords:
        glVertex3fv(vertex)
    glEnd()

def draw_floor_and_ceiling():
    # Floor (dark)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(60, 0, 0)
    glVertex3f(60, 0, 12)
    glVertex3f(0, 0, 12)
    glEnd()

    # Ceiling (light)
    glColor3f(0.75, 0.75, 0.75)
    glBegin(GL_QUADS)
    glVertex3f(0, 5, 0)
    glVertex3f(60, 5, 0)
    glVertex3f(60, 5, 12)
    glVertex3f(0, 5, 12)
    glEnd()


def draw_gun_fps():
    glPushMatrix()
    
    # Position gun: slightly right, down, and forward
    glTranslatef(0.2, -0.3, -0.8)

    # Gun Body
    glPushMatrix()
    glColor3f(0.15, 0.15, 0.15)
    gluCylinder(gluNewQuadric(), 0.07, 0.07, 0.2, 32, 8)
    glPopMatrix()

    # Barrel
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.1)
    glTranslatef(0.0, 0.0, 0.2)
    gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.6, 32, 8)
    glPopMatrix()

    # Grip
    glPushMatrix()
    glColor3f(0.12, 0.12, 0.12)
    glTranslatef(0.0, -0.15, 0.05)
    glRotatef(75, 1, 0, 0)
    glScalef(0.08, 0.3, 0.1)
    glutSolidCube(0.5)
    glPopMatrix()

    glPopMatrix()


mouse_last_x = None
mouse_last_y = None

def mouse_motion(x, y):
    global player_yaw, player_pitch, mouse_last_x, mouse_last_y
    if mouse_last_x is None or mouse_last_y is None:
        mouse_last_x = x
        mouse_last_y = y
        return
    dx = x - mouse_last_x
    dy = y - mouse_last_y
    sensitivity = 0.2
    player_yaw += dx * sensitivity
    player_pitch -= dy * sensitivity  # Invert Y-axis for natural feel
    # Pitch limit to prevent flipping
    player_pitch = max(-89, min(89, player_pitch))
    mouse_last_x = x
    mouse_last_y = y
    glutPostRedisplay()
def draw_crosshair():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1, 0, 1, -1, 1)  # Normalized device coordinates
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    glColor3f(0, 0, 0)  
    cx, cy = 0.5, 0.5   # Center of the screen in normalized coordinates
    r_outer = 0.04
    r_inner = 0.025

    # Outer circle
    glBegin(GL_LINE_LOOP)
    for i in range(64):
        angle = 2 * math.pi * i / 64
        glVertex2f(cx + math.cos(angle) * r_outer, cy + math.sin(angle) * r_outer)
    glEnd()

    # Inner circle
    glBegin(GL_LINES)
    #up
    glVertex2f(cx, cy + r_outer)
    glVertex2f(cx, cy + r_outer + 0.03)
    # down
    glVertex2f(cx, cy - r_outer)
    glVertex2f(cx, cy - r_outer - 0.03)
    # right
    glVertex2f(cx + r_outer, cy)
    glVertex2f(cx + r_outer + 0.03, cy)
    # left
    glVertex2f(cx - r_outer, cy)
    glVertex2f(cx - r_outer - 0.03, cy)
    glEnd()

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    lx = math.sin(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
    ly = math.sin(math.radians(player_pitch))
    lz = -math.cos(math.radians(player_yaw)) * math.cos(math.radians(player_pitch))
    gluLookAt(player_pos[0], player_pos[1], player_pos[2],
              player_pos[0] + lx, player_pos[1] + ly, player_pos[2] + lz,
              0, 1, 0)
    draw_floor_and_ceiling()
    for tile in wall_tiles:
        draw_tile(tile)
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    draw_gun_fps()
    glEnable(GL_DEPTH_TEST)
    draw_crosshair()  # Draw the crosshair on top of everything
    glutSwapBuffers()

def keyboard(key, x, y):
    global player_pos
    key = key.decode("utf-8").lower()
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
    glutPostRedisplay()

def special_keys(key, x, y):
    global player_yaw
    if key == GLUT_KEY_LEFT:
        player_yaw -= yaw_speed
    elif key == GLUT_KEY_RIGHT:
        player_yaw += yaw_speed
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, w / float(h), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def create_wall_with_tiles_with_door(start, end, height=5.0, rows=2, cols=6, door_rows=[0,1], door_col=3):
    x1, z1 = start
    x2, z2 = end

    length = math.sqrt((x2 - x1)**2 + (z2 - z1)**2)
    dx = (x2 - x1) / cols
    dz = (z2 - z1) / cols
    dy = height / rows

    for row in range(rows):
        for col in range(cols):
            if row in door_rows and col == door_col:
                continue  # skip door area

            y_bottom = row * dy
            y_top = (row + 1) * dy

            x_left = x1 + col * dx
            z_left = z1 + col * dz
            x_right = x1 + (col + 1) * dx
            z_right = z1 + (col + 1) * dz

            tile = [
                (x_left, y_bottom, z_left),
                (x_right, y_bottom, z_right),
                (x_right, y_top, z_right),
                (x_left, y_top, z_left)
            ]
            wall_tiles.append(tile)

def init():
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1)

    # Room 1
    create_wall_with_tiles((0, 0), (20, 0), rows=2, cols=13)     # back wall
    create_wall_with_tiles((0, 12), (20, 12), rows=2, cols=13)   # front wall
    create_wall_with_tiles((0, 0), (0, 12), rows=2, cols=6)      # left wall

    create_wall_with_tiles_with_door((20, 0), (20, 12), rows=2, cols=6, door_rows=[0, 1], door_col=3)

    # Room 2
    create_wall_with_tiles((20, 0), (40, 0), rows=2, cols=13)
    create_wall_with_tiles((20, 12), (40, 12), rows=2, cols=13)

    # Left wall with door from Room 1
    create_wall_with_tiles_with_door((20, 0), (20, 12), rows=2, cols=6, door_rows=[0, 1], door_col=3)

    # Right wall with door to Room 3
    create_wall_with_tiles_with_door((40, 0), (40, 12), rows=2, cols=6, door_rows=[0, 1], door_col=3)

    # Room 3
    create_wall_with_tiles((40, 0), (60, 0), rows=2, cols=13)
    create_wall_with_tiles((40, 12), (60, 12), rows=2, cols=13)
    create_wall_with_tiles((60, 0), (60, 12), rows=2, cols=6)


# GLUT setup
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Wall and Gun FPS Demo")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutPassiveMotionFunc(mouse_motion)  # Mouse movement handler
    glutMainLoop()

if __name__ == "__main__":
    main()

