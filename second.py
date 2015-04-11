#import module using during the whole project
import libtcodpy as libtcod #most important the libtcod libaray provide the console control system for ascii game developing
import math
import textwrap #using in menu part
import shelve #for storing the the savedata

#screen setting
SCREEN_WIDTH = 40
SCREEN_HEIGHT = 30
LIMIT_FPS = 20 #which could be used in the real-time combat system

MAP_WIDTH = 40
MAP_HEIGHT = 20

PANEL_HEIGHT = 5

tile_name_property_dict = {'floor':['.', libtcod.darker_red, False], 
                               'wall':['#', libtcod.white, True], 
                               'grass':['.', libtcod.green, False], 
                               'tree':['T', libtcod.green, True],
                               'water':['w', libtcod.blue, True]}


def main_menu():
    make_map()
    play_game()

def play_game():
    global key, mouse

    # initialize the mouse and key with libtcod libaray
    mouse = libtcod.Mouse()
    key = libtcod.Key()
    
    while not libtcod.console_is_window_closed():
        #check the input from the keyboard or mouse
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
        #display all (include the tile and objects)
        render_all()
        libtcod.console_flush()
        
        #handle the keyboard or mouse input 
        #player_action = handle_keys()

def render_all():
    #draw all the map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            map[x][y].draw(x,y)

    #draw all objects in the list
    for object in objects:
        if object != player:
            object.draw()
    player.draw()    
    
    #blit the contents of "con" to the root console and present it
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)


#######################################################################################################
# Map build
#######################################################################################################


def make_map(): #create a map with tiles
    global map, objects
    #fill the map with floor
    map = [[ Tile('floor')
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH)]
    objects = []
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            dice = libtcod.random_get_int(0, 0, 100)
            if dice <= 2:
                map[x][y].change_tile('tree')
            elif dice <= 20:
                map[x][y].change_tile('grass')
    make_room()

class Tile:
    #a tile of the map and its properties
    #one dictionary to hold the tile properties
    
     
    def __init__(self, name = 'floor'):
        self.name = name
        [self.char, self.color, self.block] = tile_name_property_dict[self.name]
        self.block_sight = self.block

    def draw(self, x, y):
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, x, y, self.char, libtcod.BKGND_NONE)

    def change_tile(self, name):
        if self.name != name:
            self.name = name
            [self.char, self.color, self.block] = tile_name_property_dict[self.name]
            self.block_sight = self.block

class Rect:
    #a rectangle on the map, used to charactize a room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)
    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1)

def make_room():
    w = libtcod.random_get_int(0, 6, 10)
    h = libtcod.random_get_int(0, 6, 10)
    x = libtcod.random_get_int(0, 0, MAP_WIDTH - w)
    y = libtcod.random_get_int(0, 4, MAP_HEIGHT - h)
    new_room = Rect(x, y, w, h)
    create_room(new_room)

def create_room(room):
    global player
    #create room
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            map[x][y].change_tile('floor')
            if x == room.x1 or x == room.x2-1 or y == room.y1 or y == room.y2-1:
                map[x][y].change_tile('wall')
    (cx, cy) = room.center()
    player = Object(cx, cy, '@', 'player', libtcod.white)
    objects.append(player)
            
######################################################################################################################
# Object build
######################################################################################################################   
            
class Object:
    #this is a generic object: the player, a monster, an item, the stairs... it always represented by a character on screen
    def __init__(self, x, y, char, name, color, blocks = False, always_visible = False, fighter = None, ai = None, item = None, equipment = None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.always_visible = always_visible
        self.equipment = equipment
        if self.fighter:
            self.fighter.owner = self
        if self.ai:
            self.ai.owner = self
        if self.item:
            self.item.owner = self
        if self.equipment:
            self.equipment.owner = self
            self.item = Item()
            self.item.owner = self

    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        #if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or (self.always_visible and map[self.x][self.y].explored)):
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
            

    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    def move_toward(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        #normalize it to length 1
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def send_to_back(self):
        #make this object be drawn first, so all others apprear above it if they're in the same tile
        global objects
        objects.remove(self)
        objects.insert(0, self)        
        

#system initalize
#load the font to display in this game, could be further implement to the graphic tiles
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

#initial the root console (direct show as screen to all the players)--width, height, title, and fullscreen or not
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Haiming second test', False)

#if the game is the turn base, this line will have no effect
libtcod.sys_set_fps(LIMIT_FPS)

#create another console
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)

#create another pane
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

main_menu()

