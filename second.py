#second.py
#import module using during the whole project
import libtcodpy as libtcod #most important the libtcod libaray provide the console control system for ascii game developing
import math
import textwrap #using in menu part
import shelve #for storing the the savedata
import copy
#from item import *

#screen setting
SCREEN_WIDTH = 70
SCREEN_HEIGHT = 40
LIMIT_FPS = 20 #which could be used in the real-time combat system

MAP_WIDTH = 180
MAP_HEIGHT = 140

DISPLAY_WIDTH = 50
DISPLAY_HEIGHT = 30

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 10
PANEL_HEIGHT = 10
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

PANEL2_WIDTH = 20
PANEL2_HEIGHT = SCREEN_HEIGHT - PANEL_HEIGHT
PANEL2_X = SCREEN_WIDTH - PANEL2_WIDTH

FOV_ALGO = 0 #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 20

#sizes of messagespa
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50

HEAL_AMOUNT = 10


CHARACTER_SCREEN_WIDTH = 30


tile_name_property_dict = {'floor':['.', libtcod.darker_red, False], 
                               'wall':['#', libtcod.white, True], 
                               'grass':['.', libtcod.green, False], 
                               'tree':['T', libtcod.green, True],
                               'water':['~', libtcod.blue, True],
                               'concrete_floor':['.', libtcod.light_blue, False],
                               'concrete_wall':['#', libtcod.light_blue, True],
                               'void':[' ', libtcod.black, True]}

career_skill_dict = {'soldior':{1:'hello'},
                     'student':{1:'learn', 2:'study'}}

career_passive_dict = {'soldior':{1:'gun skills'},
                     'student':{1:'haha', 2:'hoho'}}

def f_hello(sfrom):
    message("I am so happy!")

def f_shot(sfrom):
    message("shot, shot, shot!!!!")

def f_reload(sfrom):
    message("reload the ammo")

def f_learn(sfrom):
    message("learning......")

def f_study(sfrom):
    message("good good study, day day up")
    
skills_dict = {'hello':f_hello, 'shot':f_shot, 'reload':f_reload, 'learn':f_learn, 'study':f_study}


def main_menu():
    make_map()
    make_home()
    create_player()
    create_monster()
    create_item()
    initialize_fov()
    play_game()

#main game loop
def play_game():
    global key, mouse, game_state, game_msgs, map_state, inventory
    game_state = 'playing'
    map_state = 'map'
    game_msgs = []
    inventory = []
    equipment_component = Equipment(slot = 'right hand', add_equipment_skill = ('shot', 'reload'))
    gun = Object(1, 1, '/', 'gun', libtcod.sky, equipment = equipment_component)
    inventory.append(gun)
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
def create_item():
    #put monster
    count = 0
    while count <= 10:
        x = libtcod.random_get_int(0, 1, MAP_WIDTH - 1)
        y = libtcod.random_get_int(0, 1, MAP_HEIGHT - 1)
        if not is_blocked(x, y):
            potion_item = Item(use_function = cast_heal)
            potion = Object(x, y, '!', 'potion', libtcod.white, blocks = False, item = potion_item)
            objects.append(potion)
            count += 1


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
    fighter_status = Status('soldior', 2, 2, 2, 2)
    player_fighter = Fighter(20, 3, 0, status = fighter_status, death_function = player_death)
    player = Object(cx, cy, '@', 'player', libtcod.white, fighter= player_fighter)
    objects.append(player)

#handle the input from keyboard and mouse
def handle_keys():
    global fov_recompute, game_state, player_action, key, map, objects, home, home_objects, old_map, old_objects, map_state, old_x, old_y

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
                if map_state == 'map': 
                    old_map = map
                    old_objects = objects
                    map = home
                    objects = home_objects
                    old_x = player.x
                    old_y = player.y
                    player.x = MAP_WIDTH/2
                    player.y = MAP_HEIGHT/2
                    map_state = 'home'
                elif map_state == 'home':
                    map = old_map
                    objects = old_objects
                    player.x = old_x
                    player.y = old_y
                    map_state = 'map'
            if key_char == 'g':
                #pick up an item
                for object in objects: #look for item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up()
                        break
            if key_char == 'd':
                #show the inventory
                chosen_item = inventory_menu('Press the key next to an item to drop, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()
            if key_char == 'i':
                #show the inventory
                chosen_item = inventory_menu('Press the key next to an item to use, or any other to cancel.\n') 
                if chosen_item is not None:
                    chosen_item.use()
            if key_char == 'a':
                watch()
            if key_char >= '0' and key_char <= '9':
                use_skills(key_char)
            if key_char == 'c':
                 #show character information
                msgbox('Charact Information\n\n' + 'Maximum HP: ' + str(player.fighter.max_hp) + \
                       '\nAttack: ' + str(player.fighter.attack) + '\nDefense: '+ str(player.fighter.defense), CHARACTER_SCREEN_WIDTH)  
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

def target_tile(max_range = None):
    #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None, None) if right-clicked.
    global key, mouse, objects
    message('Please choose the target', libtcod.white)
    while True:
        #render the screen. this erase the inventroy and shows the names of object under the mouse.
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
        
        (x, y) = (mouse.cx + dis_x, mouse.cy + dis_y) #cx and cy are coordinates for the display screen which need to convert to map coordinate
         
        aim_indictor = Object(x, y, '*', 'aim_indictor', libtcod.white)
        objects.append(aim_indictor)
        render_all()
        objects.remove(aim_indictor)
        
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)

def target_monster(max_range = None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None: 
            return None
        for obj in objects:
            if obj.x == x and obj.y == y:
                return obj

def watch():
    (x, y) = target_tile()
    if x is not None:
        name = map[x][y].name
    for obj in objects:
        if obj.x == x and obj.y == y:
                name += ', '
                name += obj.name
    message(name, libtcod.green)

def msgbox(text, width = 50):
    menu(text, [], width) #use menu() as a sort of "message box"
       
def use_skills(key_num):
    num = ord(key_num) - ord('0')
    if num == 0: num = 10
    if num > len(player.fighter.total_skills):
        message('No skill in slot ' + str(num) + ' !')
        return
    skill_name = player.fighter.total_skills[num][0]
    skill_from = player.fighter.total_skills[num][1]
    cast_skill_function = skills_dict[skill_name]
    if cast_skill_function is not None:
        cast_skill_function(skill_from)

 
#######################################################################################################
# Map build
#######################################################################################################
def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True
    #fov: field of view
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
    libtcod.console_clear(con)

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
###########
#equipment
###########
def get_equipped_in_slot(slot): #return the equipment in a slot, or None if it's empty
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None

def get_all_equipped(obj): #return a list of equipped items
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []

class Equipment:
    #object that can be equiped, yielding bonuses, automatically adds the Item component.
    def __init__(self, slot, power_bonus = 0, defense_bouns = 0, max_hp_bouns = 0, add_equipment_skill = None):
        self.slot = slot
        self.is_equipped = False
        self.power_bouns = power_bonus
        self.defense_bouns = defense_bouns
        self.max_hp_bouns = max_hp_bouns
        self.add_equipment_skill = add_equipment_skill

    def toggle_equip(self):
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()

    def equip(self):
        #if the slot is already being used, dequip whatever is there first
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()
        #equip object and show message about it
        self.is_equipped = True
        message('Equipped ' + self.owner.name + ' on' + self.slot + '.', libtcod.light_green)
        
    def dequip(self): 
        #dequip object and show message about it
        self.is_equipped = False
        message('Dequipped ' + self.owner.name + ' from' + self.slot + '.', libtcod.light_yellow)
        
###########
#item
###########
def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health', libtcod.red)
        return 'cancelled'
    message('You wound start to fell better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

class Item:
    global inventory
    def __init__(self, use_function = None):
        self.use_function = use_function
    def use(self):
        #just call the use_function if it defined
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return
        if self.use_function is None:
            message('The' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner) #destory after use, unless it was cancelled for some reason

    #an item can be picked up and used
    def pick_up(self):
        #add to the player's inventory and remove from map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up' + self.owner.name + '.', libtcod.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)
        equipment = self.owner.equipment
        if equipment and get_equipped_in_slot(equipment.slot) is None:
            equipment.equip()

    def drop(self):
        #add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)
        if self.owner.equipment:
            self.owner.equipment.dequip()
###########
#fighter
###########
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

def init_skills(career):
    skills = career_skill_dict[career]
    l = len(skills)
    for key in skills:
        skills[key] = (skills[key], career)
    return (skills, l)

def init_passives(career):
    passives = career_passive_dict[career]
    n = len(passives)
    return (passives, n)   
    
class Status:
    def __init__(self, career = None, Str = 1, Con = 1, Dex = 1, Int = 1):
        self.Str = Str
        self.Con = Con
        self.Dex = Dex
        self.Int = Int
        self.skills = {}
        self.passives = {}
        self.skills_index = 0
        self.passive_index = 0
        if career is not None:
            self.career = career
            (self.skills, self.skills_index) = init_skills(career)
            (self.passives, self.passives_index) = init_passives(career)
            print career
            print self.skills
            print self.skills_index
            print self.passives
            print self.passives_index

    def change_career(self, target_career):
        self.career = target_career
        (self.skills, self.skills_index) = (target_career)
        (self.passives, self.passives_index) = init_passives(career)

    
                
    
    
    
    
   
class Fighter:
    def __init__(self, hp, attack, defense, status = Status(), xp = 0, death_function = None):
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.xp = xp
        self.death_function = death_function
        self.status = status
    
    @property
    def total_skills(self):
        
        t_skills = copy.copy(self.status.skills)
        
        for equipment in get_all_equipped(self.owner):
            if equipment.add_equipment_skill is not None:
                for skill in equipment.add_equipment_skill:
                    index = len(t_skills)
                    index += 1
                    t_skills[index] = [skill, equipment.owner.name]

        return t_skills 

    def heal(self, val):
        self.hp += val
        if(self.hp >= self.max_hp):
            self.hp = self.max_hp
        
        

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
###########
#ai
###########
class BasicMonster:
    def take_turn(self):
        #AI for all basic monster take turn.
        monster = self.owner

        if monster.distance_to(player) >= 2:
            monster.move_toward(player.x, player.y)
        else:
            monster.fighter.attack_to(player)

###########
#basic object
###########                    
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
        if libtcod.map_is_in_fov(fov_map, self.x, self.y): 
            #or (self.always_visible and map[self.x][self.y].explored)):
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
def panel2_display():
    str_s = 'Str:' + str(player.fighter.status.Str)
    con_s = 'Con:' + str(player.fighter.status.Con)
    dex_s = 'Dex:' + str(player.fighter.status.Dex)
    int_s = 'Int:' + str(player.fighter.status.Int)
    car_s = player.fighter.status.career
    panel2_msgs = [player.name, str_s, con_s, dex_s, int_s, ' ', 'career', car_s, ' ']
    skill_msgs = ['Skills:']
    #print skills
    s = player.fighter.total_skills
    for index in s:
        skill_msgs.append(str(index) + ')' + s[index][0] + ' [' + s[index][1] + ']')

    passive_msgs = ['','Passive:']
    #print passive
    for index in player.fighter.status.passives:
        passive_msgs.append(player.fighter.status.passives[index])
    
    panel2_msgs.extend(skill_msgs)
    panel2_msgs.extend(passive_msgs)
    
    libtcod.console_set_default_background(panel2, libtcod.black)
    libtcod.console_clear(panel2)
    
    y = 1
    for lines in panel2_msgs:
        libtcod.console_set_default_foreground(panel2, libtcod.white)
        libtcod.console_print_ex(panel2, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, lines)
        y += 1
   
    libtcod.console_blit(panel2, 0 , 0, PANEL2_WIDTH, PANEL2_HEIGHT, 0 ,PANEL2_X, 0)

def render_all():
    global game_msgs, fov_recompute, dis_x, dis_y
    #draw all the map
    
    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
    
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            if visible:
                libtcod.console_set_char_background(con, x, y, libtcod.darkest_grey, libtcod.BKGND_SET)
                map[x][y].draw(x,y)
            else:
                libtcod.console_set_char_background(con, x, y, libtcod.black, libtcod.BKGND_SET)   
                libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
    
                

    #draw all objects in the list
    for object in objects:
        if object != player:
            object.draw()
    player.draw()
  
    fov_recompute = True    
    
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
    #show message at panel2
    panel2_display()


    
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

def menu(header, options, width):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
    #calculate the total height for the header and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height
    #create an off-screen console that represent the menu's window
    window = libtcod.console_new(width, height)
    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
    #print all the option
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ')' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
    #blit the contents of 'window' to the root console
    x = SCREEN_WIDTH / 2 - width / 2
    y = SCREEN_HEIGHT / 2 - height / 2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    #present the root console to the player and wait for a key press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None

def inventory_menu(header):
    global inventory
    #show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for item in inventory:
            text = item.name
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)
    index = menu(header, options, INVENTORY_WIDTH)
    #if an item was chosen return it
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

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

#create another panel
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

#create second panel
panel2 = libtcod.console_new(PANEL2_WIDTH, PANEL2_HEIGHT)

main_menu()

