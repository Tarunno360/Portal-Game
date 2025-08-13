from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# Window and camera settings
width, height = 800, 600
cam_pos = [5.0, 2.0, 20.0]
cam_yaw = 0.0
cam_speed = 0.5
yaw_speed = 2.0

# Global list to track each wall tile's coordinates
wall_tiles = []

def create_wall_with_tiles(start, end, height=5.0, rows=2, cols=15):
    
    x1, z1 = start
    x2, z2 = end

    length = math.sqrt((x2 - x1)**2 + (z2 - z1)**2)
    dx = length / cols
    dy = height / rows

    # Ensure height of tile > width
    if dy <= dx:
        ratio = dx / dy
        cols = int(cols * ratio * 1.2)  # Increase cols so width shrinks
        dx = length / cols

    dz = (z2 - z1) / cols
    dx = (x2 - x1) / cols

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
    # Floor (blackish)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(20, 0, 0)
    glVertex3f(20, 0, 12)
    glVertex3f(0, 0, 12)
    glEnd()

    # Ceiling (ash)
    glColor3f(0.75, 0.75, 0.75)
    glBegin(GL_QUADS)
    glVertex3f(0, 5, 0)
    glVertex3f(20, 5, 0)
    glVertex3f(20, 5, 12)
    glVertex3f(0, 5, 12)
    glEnd()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    lx = math.sin(math.radians(cam_yaw))
    lz = -math.cos(math.radians(cam_yaw))
    gluLookAt(cam_pos[0], cam_pos[1], cam_pos[2],
              cam_pos[0] + lx, cam_pos[1], cam_pos[2] + lz,
              0, 1, 0)

    draw_floor_and_ceiling()

    for tile in wall_tiles:
        draw_tile(tile)

    glutSwapBuffers()

def keyboard(key, x, y):
    global cam_pos
    key = key.decode("utf-8").lower()
    lx = math.sin(math.radians(cam_yaw))
    lz = -math.cos(math.radians(cam_yaw))

    if key == 'w':
        cam_pos[0] += lx * cam_speed
        cam_pos[2] += lz * cam_speed
    elif key == 's':
        cam_pos[0] -= lx * cam_speed
        cam_pos[2] -= lz * cam_speed
    elif key == 'a':
        cam_pos[0] += lz * cam_speed
        cam_pos[2] -= lx * cam_speed
    elif key == 'd':
        cam_pos[0] -= lz * cam_speed
        cam_pos[2] += lx * cam_speed
    glutPostRedisplay()

def special_keys(key, x, y):
    global cam_yaw
    if key == GLUT_KEY_LEFT:
        cam_yaw -= yaw_speed
    elif key == GLUT_KEY_RIGHT:
        cam_yaw += yaw_speed
    glutPostRedisplay()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, w / float(h), 1, 100)
    glMatrixMode(GL_MODELVIEW)

def init():
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.2, 1)
    #room1
    # Define 4 walls made of tiles (forming one room)
    create_wall_with_tiles((0, 0), (20, 0), rows=2, cols=13)     # back wall
    create_wall_with_tiles((0, 12), (20, 12), rows=2, cols=13)   # front wall
    create_wall_with_tiles((0, 0), (0, 12), rows=2, cols=6)     # left wall
    create_wall_with_tiles((20, 0), (20, 12), rows=2, cols=6) # right wall

# GLUT setup
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(width, height)
glutCreateWindow(b"Tiled Walls in OpenGL")
init()
glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_keys)
glutMainLoop()
