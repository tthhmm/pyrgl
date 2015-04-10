#put this python roguelike to git
import libtcodpy as libtcod
import math
import textwrap
import shelve

#screen setting
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 43
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
MAX_ROOM_ITEMS = 2

game_state = 'playing'
player_action = None

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

#sizes of messages
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50

HEAL_AMOUNT = 40

LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5

CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 5
 
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25

#experience and level - ups
LEVEL_UP_BASE =200
LEVEL_UP_FACTOR = 150
LEVEL_SCREEN_WIDTH = 40

CHARACTER_SCREEN_WIDTH = 30


class Equipment:
    #object that can be equiped, yielding bonuses, automatically adds the Item component.
    def __init__(self, slot, power_bonus = 0, defense_bouns = 0, max_hp_bouns = 0):
        self.slot = slot
        self.is_equipped = False
        self.power_bouns = power_bonus
        self.defense_bouns = defense_bouns
        self.max_hp_bouns = max_hp_bouns

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
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or (self.always_visible and map[self.x][self.y].explored)):
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

class Fighter:
    #combat-related properties and methods (monster, player, NPC)
    def __init__(self, hp, defense, power, xp, death_function = None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.death_function = death_function
        self.xp = xp
        
    @property
    def power(self):
        bonus = sum(equipment.power_bouns for equipment in get_all_equipped(self.owner))
        return self.base_power + bonus
    
    @property
    def defense(self):
        bonus = sum(equipment.defense_bouns for equipment in get_all_equipped(self.owner))
        return self.base_defense + bonus
   
    @property
    def max_hp(self):
        bonus = sum(equipment.max_hp_bouns for equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus

    def heal(self, amount):
        #heal by given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        

    def take_damage(self, damage):
        #apply damage to self
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)
            if self.owner != player:
                player.fighter.xp += self.xp

    def attack(self, target):
        #simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            #make the target some damage
            print self.owner.name.capitalize() + ' attacks' + target.name + ' for' + str(damage) + ' hit points.'
            message(self.owner.name.capitalize() + ' attacks' + target.name + ' for' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
            
          
        else:
            print self.owner.name.capitalize() + ' attacks' + target.name + ', but it has no effect!'
            message(self.owner.name.capitalize() + ' attacks' + target.name + ', but it has no effect!')

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
                monster.fighter.attack(player)

class ConfusedMonster:
    def __init__(self, old_ai, num_turns = CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
    def take_turn(self):
        if self.num_turns > 0:
            #AI for confused monster
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
        else:
            self.owner.ai = self.old_ai
            message('The' + self.owner.name + ' is no longer confused', libtcod.red)        


class Item:
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

def get_equipped_in_slot(slot): #return the equipment in a slot, or None if it's empty
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None
            

def get_name_under_mouse():
    global mouse
    #return a string with the name of all object under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    #create a list with the names of all objects at the mouse's corrdinates nad in FOV
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)] 
    names = ', '.join(names) #join the name, separated by commas
    return names.capitalize()

def handle_keys():
    global fov_recompute, game_state, player_action, key

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
        else:
            #test for other keys
            key_char = chr(key.c)
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
            if key_char == '<':
                #go down stairs, if player is on them
                if stairs.x == player.x and stairs.y == player.y:
                    next_level()
                    message('You move down on stairs.')
                else:
                    message('You cannot find way to downstairs!')
            if key_char == 'c':
                #show character information
                level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                msgbox('Charact Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) + \
                       '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) + \
                       '\nAttack: ' + str(player.fighter.power) + '\nDefense: '+ str(player.fighter.defense), CHARACTER_SCREEN_WIDTH)
            return 'didnt-take-turn'
    

def render_all():
    global fov_map, fov_recompute, color_dark_wall, color_dark_ground, color_light_wall, color_light_ground
    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

    #draw all the map(tile)   
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
        if object != player:
            object.draw()
    player.draw()
    #blit the contents of "con" to the root console and present it
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    #prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(dungeon_level))
    #show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
    #display names of object under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_grey)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_name_under_mouse())
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1
    libtcod.console_blit(panel, 0 , 0, SCREEN_WIDTH, PANEL_HEIGHT, 0 ,0, PANEL_Y)
    

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

def random_choice_index(chances): #choose one option from list of chances, return its index
    #the dice will land on some number between 1 and the sum of chance
    dice = libtcod.random_get_int(0, 1, sum(chances))

    #go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
        if dice <= running_sum:
            return choice
        choice += 1

def random_choice(chances_dict):
    chances = chances_dict.values()
    strings = chances_dict.keys()
    return strings[random_choice_index(chances)]
    

def place_objects(room):
    max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]])
    #chance of each monster
    monster_chances = {}
    monster_chances['orc'] = 80
    monster_chances['troll'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])

    max_items = from_dungeon_level([[1, 1,], [2, 4]])

    item_chances = {}
    item_chances['heal'] = 35
    item_chances['sword'] = from_dungeon_level([[15, 1]])
    item_chances['shield'] = from_dungeon_level([[15, 1]])
    item_chances['lightning'] = from_dungeon_level([[25, 4]])
    item_chances['fireball'] = from_dungeon_level([[25, 6]])
    item_chances['confuse'] = from_dungeon_level([[10, 2]])
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, max_monsters)

    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
        if not is_blocked(x, y):
            #monster_chances = {'orc': 80, 'troll':20}
            choice = random_choice(monster_chances)
            if choice == 'orc':
                fighter_component = Fighter(hp = 20, defense = 0, power = 4,xp = 35, death_function = monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks = True, fighter = fighter_component, ai = ai_component)
            elif choice == 'troll':
                fighter_component = Fighter(hp = 30, defense = 2, power = 8, xp = 100, death_function = monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green, blocks = True, fighter = fighter_component, ai = ai_component)
            objects.append(monster)
    
    #choose random number of items
    num_items = libtcod.random_get_int(0, 0, max_items)
    for i in range(num_items):
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
        if not is_blocked(x, y):
            #item_chances = {'heal':70, 'lightning':10, 'fireball':10, 'confuse':10}
            choice = random_choice(item_chances)
            if choice == 'heal':
                #create a healing potion
                item_component = Item(use_function = cast_heal)
                item = Object(x, y, '!', 'healing potion', libtcod.violet, always_visible = True, item  = item_component)
            elif choice == 'lightning':
                #create a lightning bolt scroll
                item_component = Item(use_function = cast_lightning)
                item = Object(x, y, '!', 'scroll of lightning bolt', libtcod.light_yellow, always_visible = True, item = item_component)
            elif choice == 'fireball':
                #create a fireball scroll
                item_component = Item(use_function = cast_fireball)
                item = Object(x, y, '!', 'scroll of fireball', libtcod.light_yellow, always_visible = True, item = item_component)
            elif choice == 'confuse':
                #create a confused scroll
                item_component = Item(use_function = cast_confuse)
                item = Object(x, y, '!', 'scroll of confusion', libtcod.light_yellow, always_visible = True, item = item_component)
            elif choice == 'sword':
                equipment_component = Equipment(slot = 'right hand', power_bonus = 4)
                item = Object(x, y, '/', 'sword', libtcod.sky, equipment = equipment_component)
            elif choice == 'shield':
                equipment_component = Equipment(slot = 'left hand', defense_bouns = 1)
                item = Object(x, y, '/', 'shield', libtcod.sky, equipment = equipment_component)
            objects.append(item)
            item.send_to_back() #items appear below other objects
                

def is_blocked(x, y):
    #block by tile
    if map[x][y].blocked:
        return True
    #block by objects
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            return True
    return False

def player_move_or_attack(dx, dy):
    global fov_recompute
    x = player.x + dx
    y = player.y + dy

    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break;

    if target is not None:
        player.fighter.attack(target)
    else: 
        player.move(dx, dy)
        fov_recompute = True

def make_map():
    global map, objects, stairs
    #the list of objects with just the player
    objects = [player]

    #fill map with unblocked tiless
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
            #room_no = Object(new_x, new_y, chr(65 + num_rooms),'room_number', libtcod.white)
            #objects.insert(0, room_no)
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
                #stairs = Object(new_x-1, new_y-1, '<', 'stair', libtcod.white)
                #objects.append(stairs)
                #stairs.send_to_back() #so it's drawn below the monsters
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
    #create stairs at the center of the last room
    stairs = Object(new_x, new_y, '<', 'stair', libtcod.white, always_visible = True)
    objects.append(stairs)
    stairs.send_to_back() #so it's drawn below the monsters


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
    print monster.name.capitalize() + 'is dead!'
    message(monster.name.capitalize() + 'is dead! You gain ' + str(monster.fighter.xp) + ' experience points', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.block = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()

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

def message(new_msg, color = libtcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
    for line in new_msg_lines:
        #if the buffer is full, remove thefirst line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
        #add the new line as tuple, with the text and color
        game_msgs.append((line, color))

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
    

def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health', libtcod.red)
        return 'cancelled'
    message('You wound start to fell better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
    #find close enemy and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None: #no enemy found with maximum range
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'

    #zap it!
    message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is ' + str(LIGHTNING_DAMAGE) + ' hit points', libtcod.red)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

def closest_monster(max_range):
    #find the closest enemy, up to max_range in the FOV
    closest_enemy = None
    closest_dist = max_range + 1 #start with (slightly more than) maximum range
    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
        #calculate the distance between this object and the player
            dist = player.distance_to(object)
            if dist < closest_dist: #it's closer, remember it
                closest_dist = dist
                closest_enemy = object
    return closest_enemy

def cast_confuse():
    #find closest enemy in range and confuse it
    message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'canncelled'

    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster #tell the new component who owns it
    message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around', libtcod.light_green)

def target_tile(max_range = None):
    #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None, None) if right-clicked.
    global key, mouse
    while True:
        #render the screen. this erase the inventroy and shows the names of object under the mouse.
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
        render_all()
        (x, y) = (mouse.cx, mouse.cy)
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)

def cast_fireball():
    #ask the player for a target tile for the fireball
    message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)

    for obj in objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + 'gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points', libtcod.orange)
            obj.fighter.take_damage(FIREBALL_DAMAGE)

def target_monster(max_range = None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None: 
            return None
        for obj in objects:
            if obj.x == x and obj.y == y:
                return obj


def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level, stairs
    #create object representing the player
    fighter_component = Fighter(hp = 100, defense = 1, power = 4, xp = 0, death_function = player_death)
    player = Object(0, 0, '@', 'player', libtcod.white, blocks = True, fighter = fighter_component)
    player.level = 1
    
    #create a map
    dungeon_level = 1
    make_map()
    initialize_fov()

    #create a inventory to hold all the items
    inventory = []
    
    #create the list of game message and their colors, starts empty
    game_msgs = []
    
    game_state = 'playing'

    #a warm welcome message!
    message('Welcome stranger! Prepare ot perish in the Tomb of the Ancient Kings.', libtcod.red)

def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True
    #fov: field of view
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
    libtcod.console_clear(con)

def play_game():
    global key, mouse
    #main game loop

    #mouse and key
    mouse = libtcod.Mouse()
    key = libtcod.Key()

    while not libtcod.console_is_window_closed():
   
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
    
        render_all()
        libtcod.console_flush()
        check_level_up()
   
        #erase all objects at their old location, before they move
        for object in objects:
            object.clear()
        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break

        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()

def main_menu():
    img = libtcod.image_load('menu_background.png')
    while not libtcod.console_is_window_closed():
        #show the background image, a twice the regular console resolution
        libtcod.image_blit_2x(img, 0, 0, 0)
        
        #show the game's title, and some credits!
        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER, 'TOMBS OF THE ANCIENT KINGS')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER, 'By Haiming')

        #show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)
        if choice == 0: #new game
            new_game()
            play_game()
        elif choice == 1: #load game
            try:
                load_game()
            except:
                msgbox('\n No save game to load. \n', 24)
                continue
            play_game()
            
        elif choice == 2: #quit
            break
    
def save_game():
    #open a new empty shelve (possible overwriting and old one) to write the game data
    file = shelve.open('savegame', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['stairs_index'] = objects.index(stairs)
    file['dungeon_level'] = dungeon_level
    file.close()    

def next_level():
    global dungeon_level
    #advance to next level
    message('You take a monent to rest, and recover your health', libtcod.light_violet)
    player.fighter.heal(player.fighter.max_hp / 2)
    message('After a rare moment of peach, you descent deeper into the heart of dungeon...', libtcod.red)
    dungeon_level += 1
    make_map()
    initialize_fov()    
    
def load_game():
    global map, objects, player, inventory, game_msgs, game_state, stairs, dungeon_level
    #open the previously saved shelve and load the game data
    file = shelve.open('savegame', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    stairs = objects[file['stairs_index']]
    dungeon_level = file['dungeon_level']
    file.close()
    initialize_fov()

def msgbox(text, width = 50):
    menu(text, [], width) #use menu() as a sort of "message box"    

def check_level_up():
    #see if the player's experience is enough to level up
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        #it is! level up
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('You battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)
        choice = None
        while choice == None:
            choice = menu('Level up! Choose a stat to raise:\n', ['Consitiution (+ 20 HP, from ' + str(player.fighter.max_hp) + ')', \
                         'Strength (+ 1 attack, from ' + str(player.fighter.power) + ')', \
                         'Agility (+ 1 defense, from ' + str(player.fighter.defense) + ')'], LEVEL_SCREEN_WIDTH)
            if choice == 0:
                player.fighter.base_max_hp += 20
            elif choice == 1:
                player.fighter.base_power += 1
            elif choice == 2:
                player.fighter.base_defense += 1

def from_dungeon_level(table):
    #return a value that depends on level. the table specifies what value occurs after each level, defaultis 0
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0

def get_all_equipped(obj): #return a list of equipped items
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []

#load the font to display
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

#initial the console screen--width, height, title, and fullscreen or not
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)

#if the game is the turn base, this line will have no effect
libtcod.sys_set_fps(LIMIT_FPS)

#create another console
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)

panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

main_menu()






    

