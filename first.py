#put this python roguelike to git
import libtcodpy as libtcod
import math

#screen setting
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45
color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_wall = libtcod.Color(130, 110, 50)
color_light_ground = libtcod.Color(200, 180, 50)

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

FOV_ALGO = 0 #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

MAX_ROOM_MONSTERS = 3

game_state = 'playing'
player_action = None

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
    
class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight
        self.explored = False


class Object:
    #this is a generic object: the player, a monster, an item, the stairs... it always represented by a character on screen
    def __init__(self, x, y, char, name, color, blocks = False, fighter = None, ai = None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self
        self.ai = ai
        if self.ai:
            self.ai.owner = self

    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
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

class Fighter:
    #combat-related properties and methods (monster, player, NPC)
    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power

class BasicMonster:
    def take_turn(self):
        #AI for a basic monster take turn. If you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            #move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_toward(player.x, player.y)

            #close enough, attack!
            elif player.fighter.hp > 0:
                print 'The attack of the' + monster.name + 'bounces off your shiny metal armor!'        
        



def handle_keys():
    global fov_recompute, game_state, player_action

    #function key
    #key = libtcod.console_check_for_keypress() #real-time
    key = libtcod.console_wait_for_keypress(True) # turn-based
    if key.vk == libtcod.KEY_ENTER and key.lalt: #Enter+alt
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' # exit game
    
    if game_state == 'playing':
        #movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_UP):
            player_move_or_attack(0, -1)
        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player_move_or_attack(0,1)
        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player_move_or_attack(-1,0)
        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
            player_move_or_attack(1,0)
        else:
            return 'didnt-take-turn'
    

def render_all():
    global fov_map, fov_recompute, color_dark_wall, color_dark_ground, color_light_wall, color_light_ground
    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

       
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = map[x][y].block_sight
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            if not visible:
                if map[x][y].explored:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                map[x][y].explored = True
     #draw all objects in the list
    for object in objects:
        object.draw()
    #blit the contents of "con" to the root console and present it
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

def create_room(room):
    global map
    #create room
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False 
        map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def place_objects(room):
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)
        if not is_blocked(x, y):
            if libtcod.random_get_int(0, 0, 100) < 80:
                fighter_component = Fighter(hp = 10, defense = 0, power = 3)
                ai_component = BasicMonster()
             
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks = True, fighter = fighter_component, ai = ai_component)
            else:
                fighter_component = Fighter(hp = 16, defense = 1, power = 4)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green, blocks = True, fighter = fighter_component, ai = ai_component)
            objects.append(monster)

def is_blocked(x, y):
    if map[x][y].blocked:
        return True
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True
    return False

def player_move_or_attack(dx, dy):
    global fov_recompute
    x = player.x + dx
    y = player.y + dy

    target = None
    for object in objects:
        if object.x == x and object.y == y:
            target = object
            break;

    if target is not None:
        print 'The' + target.name + 'laughs at your puny efforts to attack him'
    else: 
        player.move(dx, dy)
        fov_recompute = True

def make_map():
    global map, player, objects
    #fill map with unblocked tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]
    rooms = []
    num_rooms = 0
    for r in range(MAX_ROOMS):
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
        new_room = Rect(x, y, w, h)
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
        if not failed:
            create_room(new_room)
            place_objects(new_room)
            (new_x, new_y) = new_room.center()
            room_no = Object(new_x, new_y, chr(65 + num_rooms),'room_number', libtcod.white)
            objects.insert(0, room_no)
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
            else:
                (prev_x, prev_y) = rooms[num_rooms-1].center()
                if libtcod.random_get_int(0,0,1) == 1:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            rooms.append(new_room)
            num_rooms += 1     

#load the font to display
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

#initial the console screen--width, height, title, and fullscreen or not
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)

#if the game is the turn base, this line will have no effect
libtcod.sys_set_fps(LIMIT_FPS)

#create another console
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

#create object representing the player
fighter_component = Fighter(hp = 30, defense = 2, power = 5)
player = Object(0, 0, '@', 'player', libtcod.white, blocks = True, fighter = fighter_component)
objects = [player]
make_map()

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
fov_recompute = True    

#main game loop
while not libtcod.console_is_window_closed():
   
    
    render_all()
    libtcod.console_flush()
   
    #handle keys and exit game if needed
    for object in objects:
        object.clear()
 
    player_action = handle_keys()
    if player_action == 'exit':
        break

    if game_state == 'playing' and player_action != 'didnt_take_turn':
        for object in objects:
            if object.ai:
                object.ai.take_turn()

    

