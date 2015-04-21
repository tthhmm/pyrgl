#import module using during the whole project
import libtcodpy as libtcod #most important the libtcod libaray provide the console control system for ascii game developing
import math
import textwrap #using in menu part
import shelve #for storing the the savedata

#screen setting
SCREEN_WIDTH = 50
SCREEN_HEIGHT = 30
LIMIT_FPS = 20 #which could be used in the real-time combat system

MAP_WIDTH = 80
MAP_HEIGHT = 40

DISPLAY_WIDTH = 50
DISPLAY_HEIGHT = 20

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 10
PANEL_HEIGHT = 10
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

#sizes of messages
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

tile_name_property_dict = {'floor':['.', libtcod.darker_red, False], 
                               'wall':['#', libtcod.white, True], 
                               'grass':['.', libtcod.green, False], 
                               'tree':['T', libtcod.green, True],
                               'water':['~', libtcod.blue, True],
                               'concrete_floor':['.', libtcod.light_blue, False],
                               'concrete_wall':['#', libtcod.light_blue, True],
                               'void':[' ', libtcod.black, True]}


def main_menu():
    make_map()
    make_home()
    create_player()
    create_monster()
    play_game()

#main game loop
def play_game():
    global key, mouse, game_state, game_msgs
    game_state = 'playing'
    game_msgs = []
    inventory = []
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
        player_action = handle_keys()
        if player_action == 'exit':
            break

        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()

def create_monster():
    global objects
    #put monster
    count = 0
    while count <= 10:
        x = libtcod.random_get_int(0, 1, MAP_WIDTH - 1)
        y = libtcod.random_get_int(0, 1, MAP_HEIGHT - 1)
        if not is_blocked(x, y):
            zombie_fighter = Fighter(10, 1, 0, death_function = monster_death)
            zombie_ai = BasicMonster()
            zombie = Object(x, y, 'z', 'Zombie', libtcod.white, blocks = True, fighter = zombie_fighter, ai = zombie_ai)
            objects.append(zombie)
            count += 1

def create_player():
    global player
    #create a room
    init_room = make_room()
    (cx, cy) = init_room.center()
    player_fighter = Fighter(20, 3, 0, death_function = player_death)
    player = Object(cx, cy, '@', 'player', libtcod.white, fighter= player_fighter)
    objects.append(player)

#handle the input from keyboard and mouse
def handle_keys():
    global fov_recompute, game_state, player_action, key, map, objects, home, home_objects

    #function key
    #key = libtcod.console_check_for_keypress() #real-time
    #key = libtcod.console_wait_for_keypress(True) # turn-based
    if key.vk == libtcod.KEY_ENTER and key.lalt: #Enter+alt
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' # exit game
    
    if game_state == 'playing':
        #movement keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0,1)
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1,0)
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1,0)
        elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
        elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1,-1)
        elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1,1)
        elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1,1)
        elif key.vk == libtcod.KEY_SPACE:
            return 'wait a turn' 
        else:
            #test for other keys
            key_char = chr(key.c)
            if key_char == 'h':
                old_map = map
                old_objects = objects
                map = home
                objects = home_objects
                player.x = MAP_WIDTH/2
                player.y = MAP_HEIGHT/2
            return 'didnt-take-turn'

####################################################################################################
# Some sub functions
####################################################################################################

def is_blocked(x, y):
    #block by edge
    if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT:
        return True
    #block by tile
    if map[x][y].blocked:
        return True
    #block by objects
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            return True
    return False
    

 
#######################################################################################################
# Map build
#######################################################################################################
def make_home():
    global home, home_objects
    home = [[ Tile('void')
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH)]
    home_objects = []
    #create a room
    w = 16
    h = 10
    x = MAP_WIDTH/2 - w/2
    y = MAP_HEIGHT/2 - h/2
    new_room = Rect(x, y, w, h)
    create_room(new_room, home, floor_name = 'concrete_floor', wall_name = 'concrete_wall', door = False)
    

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
    
    #create a pool
    #make_pool()
    

class Tile:
    #a tile of the map and its properties
    #one dictionary to hold the tile properties
    
     
    def __init__(self, name = 'floor'):
        self.name = name
        [self.char, self.color, self.blocked] = tile_name_property_dict[self.name]
        self.block_sight = self.blocked

    def draw(self, x, y):
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, x, y, self.char, libtcod.BKGND_NONE)

    def change_tile(self, name):
        if self.name != name:
            self.name = name
            [self.char, self.color, self.blocked] = tile_name_property_dict[self.name]
            self.block_sight = self.blocked

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
    y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h)
    new_room = Rect(x, y, w, h)
    create_room(new_room, map)
    return new_room

def make_pool():
    w = libtcod.random_get_int(0, 10, 16)
    h = libtcod.random_get_int(0, 10, 16)
    x = libtcod.random_get_int(0, 0, MAP_WIDTH - w)
    y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h)
    new_room = Rect(x, y, w, h)
    create_pool(new_room)

def create_pool(room):
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            if x+y > room.x1+room.y1+2 and x+y < room.x2 + room.y2 -4 and x-y > room.x1-room.y2+2 and x-y < room.x2-room.y1-5:  
                map[x][y].change_tile('water')
    

def create_room(room, tile_map, floor_name = 'floor', wall_name = 'wall', door = True):
    #create room
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            tile_map[x][y].change_tile(floor_name)
            if x == room.x1 or x == room.x2-1 or y == room.y1 or y == room.y2-1:
                tile_map[x][y].change_tile(wall_name)
    if door:
        #create door
        side = libtcod.random_get_int(0, 0, 3)
        if side == 0:
           tile_map[libtcod.random_get_int(0, room.x1, room.x2-1)][room.y1].change_tile('floor')
        elif side == 1:
           tile_map[libtcod.random_get_int(0, room.x1, room.x2-1)][room.y2-1].change_tile('floor')
        elif side == 2:
           tile_map[room.x1][libtcod.random_get_int(0, room.y1, room.y2-1)].change_tile('floor')
        elif side == 3:
           tile_map[room.x2-1][libtcod.random_get_int(0, room.y1, room.y2-1)].change_tile('floor')
            
######################################################################################################################
# Object build and its own component
######################################################################################################################
def player_move_or_attack(dx, dy):
    global player
    x = player.x + dx
    y = player.y + dy
    
    target = None
    for object in objects:
        if object.fighter and x == object.x and y == object.y:
            target = object
            break
    if target is not None:
        player.fighter.attack_to(target) 
    else:
        player.move(dx, dy)
   
class Fighter:
    def __init__(self, hp, attack, defense, xp = 0, death_function = None):
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.xp = xp
        self.death_function = death_function
        

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)
            if self.owner != player:
                player.fighter.xp += self.xp
    
    def attack_to(self, target):
        #simple formula for attack damage
        #print "Hello"
        damage = self.attack - target.fighter.defense
        if damage > 0:
            print (self.owner.name.capitalize() + ' attacks' + target.name + ' for' + str(damage) + ' hit points.')
            message(self.owner.name.capitalize() + ' attacks' + target.name + ' for' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else: 
            message(self.owner.name.capitalize() + ' attacks' + target.name + ', but it has no effect!')

class BasicMonster:
    def take_turn(self):
        #AI for all basic monster take turn.
        monster = self.owner

        if monster.distance_to(player) >= 2:
            monster.move_toward(player.x, player.y)
        else:
            monster.fighter.attack_to(player)
                    
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

def player_death(player):
    #end game
    global game_state
    print 'You died!!!'
    message('You died!!', libtcod.red)
    game_state = 'dead'
    #additional format
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster):
    #transformit into a nasty corpse! id doesn't block, can't be attack and doesn't move
    #print monster.name.capitalize() + 'is dead!'
    message(monster.name.capitalize() + 'is dead! You gain ' + str(monster.fighter.xp) + ' experience points', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.block = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()

####################################################################################################
# Display
####################################################################################################
def render_all():
    global game_msgs
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
    #calculate the player point
    dis_x = player.x - DISPLAY_WIDTH / 2
    dis_y = player.y - DISPLAY_HEIGHT / 2
    if dis_x < 0:
        dis_x = 0
    elif dis_x > MAP_WIDTH - DISPLAY_WIDTH:
        dis_x = MAP_WIDTH - DISPLAY_WIDTH
    if dis_y < 0:
        dis_y = 0
    elif dis_y > MAP_HEIGHT - DISPLAY_HEIGHT:
        dis_y = MAP_HEIGHT - DISPLAY_HEIGHT 
    libtcod.console_blit(con, dis_x, dis_y, DISPLAY_WIDTH, DISPLAY_HEIGHT, 0, 0, 0)
    
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    #show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
    #show message right the bar
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1
    libtcod.console_blit(panel, 0 , 0, SCREEN_WIDTH, PANEL_HEIGHT, 0 ,0, PANEL_Y)

def message(new_msg, color = libtcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
    for line in new_msg_lines:
        #if the buffer is full, remove thefirst line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
        #add the new line as tuple, with the text and color
        game_msgs.append((line, color))


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc) first calculate the width of the bar
    bar_width= int(float(value) / maximum * total_width)

    #render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    #render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
   
    #some centered text with the value
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))

########################################################################################################################################
#system initalize
########################################################################################################################################
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

