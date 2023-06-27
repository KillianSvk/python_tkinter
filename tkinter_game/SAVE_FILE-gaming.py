import tkinter as tk
import math
import random
import threading
import time
import functools

class Arena: # The Fighting Arena
    
   
    def __init__(self, root):
        # Canvas Setup
        self.canvas = tk.Canvas(root, width=1920, height=1080)
        self.canvas.pack()

        # Variables Setup
        self.threads = []
        self.player_colors = ['blue', 'red', 'green', 'yellow']
        self.mouse_hold = [] # Current unit
        self.fields = [] # All fields in Arena
        self.units = [] # All units in Arena
        self.selected = None # On what object is player pointing with mouse
        self.backtracking_result = [0] * 100 # Best possible path for unit
        self.unit_walked_fields = set() # Highlighting fields which unit can go to


        # dict of unit pngs
        self.units_png = {'Tank': {1: tk.PhotoImage(file='art/tank_1.png'), 2: tk.PhotoImage(file='art/tank_2.png'),},
                          'Warrior': {1: tk.PhotoImage(file='art/warrior_1.png'), 2: tk.PhotoImage(file='art/warrior_2.png'),},
                          'Archer': {1: tk.PhotoImage(file='art/archer_1.png'), 2: tk.PhotoImage(file='art/archer_2.png'),},
                          }
        self.unit_portrait_png = {'Tank':  tk.PhotoImage(file='art/tank_portrait.png'),
                                  'Warrior':  tk.PhotoImage(file='art/warrior_portrait.png'),
                                  'Archer':  tk.PhotoImage(file='art/archer_portrait.png'),
                                  }

        # Inputs
        self.canvas.bind('<Button-1>',self.mouse_click)
        self.canvas.bind('<Motion>', self.moving_mouse)
    
        self.draw_arena()

        self.combat_phase = False

        if self.combat_phase == False:
            self.start_fight_button = tk.Button( text='Fight', padx= 2, pady=1, font=("Helvetica", 20), borderwidth=3, background='red', activebackground='red', command= self.prepare_combat)
            self.start_fight_button.place(x=1920/2, y=50, anchor='center')

            self.units_to_select = []
            for i,color in enumerate(('red', 'gray', 'blue')):
                self.units_to_select.append(self.canvas.create_oval(700-20 + i*200,1000-20, 700+20 + i*200, 1000+20, width=3, fill=color, tags='unit_taker'))


        self.canvas.mainloop()

    def mouse_click(self, event):
        selected = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)

        if selected:
            selected = selected[0]
        
        # If you clicked on smth during preparetion phase
        if selected and self.combat_phase == False:

            if selected in self.units_to_select:
                unit = self.Unit(random.randrange(999),selected)
                self.mouse_hold = [unit]

            if selected in self.canvas.find_withtag('field') and len(self.mouse_hold) > 0 and self.fields[selected -1].occupied == None:
                # Find pos
                x,y = self.fields[selected -1].x, self.fields[selected -1].y

                # Choose player based on x-axis
                if x < 1920/2:
                    player = 1
                if x > 1920/2:
                    player = 2
                
                # Set unit
                unit = self.mouse_hold.pop()
                unit.player = player
                unit.pos = self.fields[selected -1]
                unit.draw(self.canvas, x, y)
                self.units.append(unit)

                # occupy the field the unit is stading on
                self.fields[selected -1].occupied = unit

        if selected and self.backtracking_result != [0] * 100 and selected == self.backtracking_result[-1].id:
            self.canvas.delete('unit_path')
            unit = self.mouse_hold
            # Unoccupy the starting field
            starting_field = self.backtracking_result.pop(0)
            starting_field.occupied = None

            self.canvas.delete('turn_highlight')

            for field in self.backtracking_result:
                x0,y0 = unit.pos.x, unit.pos.y
                unit.pos = field
                unit.current_actions -= 1
                x1,y1 = unit.pos.x, unit.pos.y
                self.canvas.move(unit.id, x1-x0, y1-y0)
                self.canvas.update()
                time.sleep(0.25)

            field.occupied = unit

            # if unit used all its movement then end turn
            if unit.current_actions == 0:
                self.end_turn()
            else:
                self.refresh_unit(unit)


    
    def moving_mouse(self, event):
        selected = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)

        if selected:

            # If the player is selecting the same object nothing needs to change
            if selected == self.selected:
                return
            self.selected = selected

            # Highlighting a unit with respected turn order border
            if selected[0] in self.canvas.find_withtag('turn_order_border') and selected[0] not in self.canvas.find_withtag('turn_milestone'):

                # Delete temporary borders if more then one selceted 
                if len(self.canvas.find_withtag('temporary')) > 1:
                    self.canvas.delete('temporary')

                if self.canvas.gettags(selected[0]):
                    # find unit coresponding to a border
                    unit_portarait_tag = self.canvas.gettags(selected[0])[1]
                    unit_tag = '_'.join(unit_portarait_tag.split('_')[:2])
                    unit_id = self.canvas.find_withtag(unit_tag)[0]
                    for unit in self.units:
                        if unit_id == unit.canvas_id:
                            break
                    # set right attributes for hex
                    x,y = unit.pos.x, unit.pos.y
                    color = '#00e6b8'
                    if unit == self.mouse_hold:
                        color = '#e6cf00'

                    # highlight hex and border
                    hex = self.draw_hexagon(x,y,color,'temporary')
                    # Put hex under units visualy
                    self.canvas.tag_raise(unit.id, hex)
                    for field in unit.pos.neighbor_fields:
                        for u in self.units:
                            if u.pos == field:
                                self.canvas.tag_raise(u.id, hex)

                    coords = self.canvas.coords(selected[0])
                    self.canvas.create_rectangle(*coords ,width=3, outline=color, tags='temporary')

            else:
                self.canvas.delete('temporary')

            # Controling unit and choosing where it should move
            if selected[0] in self.canvas.find_withtag('field') and self.mouse_hold and self.combat_phase == True:
                unit = self.mouse_hold
                for field in self.fields:
                    if selected[0] == field.id:
                        break
                
                self.pathfinding(unit, field, unit.current_actions)


            # hovering over a unit that you are trying to attack
            if selected[-1] in self.canvas.find_withtag('unit') and self.mouse_hold and self.combat_phase == True:
                for unit in self.units:
                    if selected[-1] == unit.canvas_id:
                        break
                
                # Look if you are not trying to attack your own units
                if self.mouse_hold.player != unit.player:
                    print(abs(self.mouse_hold.pos.col - unit.pos.col) , abs(self.mouse_hold.pos.row - unit.pos.row))

        else:
            self.canvas.delete('temporary')
            self.canvas.delete('unit_path')
            self.selected = selected
     

    def draw_arena(self):
        side_lenght = 60

        for line,y in enumerate(range(150, 950 ,int(side_lenght + side_lenght/2))):
            if line % 2 == 1:
                offset = (side_lenght * math.sqrt(3))/2
                row_lnght = 1600
            else:
                offset = 0
                row_lnght = 1700

            for row,x in enumerate(range(200, row_lnght ,int(side_lenght * math.sqrt(3)))):
                if offset != 0:
                    field = self.Field(self.canvas, line, row)
                else:
                    field = self.Field(self.canvas, line, row+1)

                # Cant place on middle parts
                if row > 1 and row < 13 - offset//50:
                    field.occupied = True

                field.draw(side_lenght, x, y, offset)
                self.fields.append(field)

    def draw_hexagon(self, x, y, color, tags=None):
        side_lenght = 60

        self.x = x = x
        self.y = y
        angle = 2 * math.pi / 6
        points = []

        for pdx in range(6):
            _angle = angle * pdx + math.pi/6
            _x = x + math.cos(_angle) * side_lenght
            _y = y + math.sin(_angle) * side_lenght
            points.append((_x, _y))
        self.id = self.canvas.create_polygon(*points, width=2, outline='black', fill=color, tags= tags)


    def prepare_combat(self): # Prepapres Arena for combat
        self.combat_phase = True

        # Place some units for testing
        for i in range(4):
            fields = filter(lambda field: field.occupied == None, self.fields)
            fields = list(fields)

            fields_1 = filter(lambda field: field.x < 1920/2, fields)
            fields_2 = filter(lambda field: field.x > 1920/2, fields)

            fields_1, fields_2 = list(fields_1), list(fields_2)
            field_1, field_2 = random.choice(fields_1), random.choice(fields_2)

            unit_choice = random.choice(('Warrior','Tank','Archer'))

            for j,field in enumerate((field_1, field_2)):
                # Set unit
                unit = self.Unit(random.randrange(10000), unit_choice, j+1)
                unit.player = j+1
                unit.pos = field
                unit.draw(self.canvas, self.units_png[unit.name][j+1])
                self.units.append(unit)

                # occupy the field the unit is stading on
                field.occupied = unit     

        if self.mouse_hold: # Empty hand if needed
            self.mouse_hold.pop() 

        # Remove fight button and Unit select
        self.start_fight_button.destroy()
        self.canvas.delete('unit_taker')

        for field in self.fields:
            field.occupied = None
            self.canvas.itemconfig(field.id, fill=field.color)
            # Print ID of field on it for testing
            # self.canvas.create_text(field.x,field.y, text=field.id, font=("Helvetica", 15))

        # Create Graph of fields
        graph_fields = [[]] # Graph for pathfinding
        offset = 0
        i = 1
        for field in self.fields:
            graph_fields[-1].append(field)

            if i + offset == 15: # Next line
                graph_fields.append([]) # Add new line to graph
                i = 0
                # Change offset
                if offset == 0:
                    offset = 1
                elif offset == 1:
                    offset = 0

            i += 1

        # Add neigbors to each Field
        for i,line in enumerate(graph_fields):
            for j,field in enumerate(line):
                # Set correct offset
                if len(line) == 15:
                    offset = False
                if len(line) == 14:
                    offset = True

                if j+1 != len(line): # Check if not last
                    # Add Field to the right to neighbors
                    field.neighbor_fields.add(line[j+1])
                    line[j+1].neighbor_fields.add(field)

                if j > 0: # Check if not first
                    # Add Field to the left to neighbors
                    field.neighbor_fields.add(line[j-1])
                    line[j-1].neighbor_fields.add(field)

                if j+1 <= len(graph_fields[i+1]): # Check if there is a field under you
                    # Add Field under you to neighbors
                    field.neighbor_fields.add(graph_fields[i+1][j])
                    graph_fields[i+1][j].neighbor_fields.add(field)

                if offset == True:
                    if len(graph_fields[i+1]) > 1: # Check if there is a field under you
                        # Add Field under you +1 to the left, to neighbors
                        field.neighbor_fields.add(graph_fields[i+1][j+1])
                        graph_fields[i+1][j+1].neighbor_fields.add(field)

                if offset == False:
                    if j > 0 and len(graph_fields[i+1]) > 1: # Check if there is a field under you
                        # Add Field under you +1 to the left, to neighbors
                        field.neighbor_fields.add(graph_fields[i+1][j-1])
                        graph_fields[i+1][j-1].neighbor_fields.add(field)

        # Organize Field neighbors
        for field in self.fields:
            field.neighbor_fields = sorted(field.neighbor_fields, key= lambda field: field.id)

        # Occupy units pos
        for unit in self.units:
            unit.pos.occupied = unit

        # Create turn order
        self.units.sort(key=lambda unit: unit.actions, reverse=True)
        self.current_turn_order = self.units.copy()

        # Skip & Delay turn buttons
        tk.Button(self.canvas, text='Skip', font=("Helvetica", 20), borderwidth=3, command= self.end_turn).place(x=150, y=1000)
        tk.Button(self.canvas, text='Delay', font=("Helvetica", 20), borderwidth=3, command= self.delay_turn).place(x=140, y=945)

        # Start Combat
        self.turn = 0
        self.combat()

    def draw_turn_order(self):
        self.canvas.delete('turn_order_border') # Delete borders from previous round
        turn_order = self.current_turn_order.copy()
        x,y = 300, 1000
        i = 0
        index = 0
        while i < 13:
            offset = 104 * i

            if index >= len(turn_order):
                index = 0
                self.canvas.create_rectangle(x+ 50 + offset,y+50,x- 50 + offset,y-50, width=3, outline='gray', fill='gray', tags=('turn_order_border','turn_milestone'))
                turn_order = self.units.copy()

            else:
                unit = turn_order[index]
                color = self.player_colors[unit.player -1]
                self.canvas.create_rectangle(x+ 50 + offset,y+50,x- 50 + offset,y-50, width=3, outline=color, fill='white', tags=('turn_order_border',f'{unit.id}_portrait'))
                self.canvas.create_image(x + offset,y, anchor='center', image= self.unit_portrait_png[unit.name], tags= 'turn_order_border')

                index += 1

            i += 1

    def end_turn(self):
        # remove unit which turn has passed
        if self.current_turn_order:
            self.current_turn_order[0].delayed = False # Reset delayed value after ending units turn
            self.current_turn_order.pop(0)

            # Remove unwanted widgets
            self.canvas.delete('turn_highlight') # Remove highlight from current unit
            self.canvas.delete('unit_path') # Remove unit path line

            # if no more units in current turn, start a new turn
            if not self.current_turn_order:
                self.current_turn_order = self.units.copy()
                self.turn += 1

        self.combat()

    def delay_turn(self):
        if self.current_turn_order[0].delayed == False: # Current unit wasnt delayed this turn
            self.current_turn_order[0].delayed = True
            self.current_turn_order.append(self.current_turn_order.pop(0))

            # Remove unwanted widgets
            self.canvas.delete('turn_highlight') # Remove highlight from current unit
            self.canvas.delete('unit_path') # Remove unit path line

            self.combat()

    # Redraw highlights every time a unit moves
    def refresh_unit(self, unit):
        # Refresh old
        for field in self.unit_walked_fields:
            self.canvas.itemconfig(field.id, fill=field.color)

        # Highlight a unit which turn it is
        hex = self.draw_hexagon(unit.pos.x, unit.pos.y, '#e6cf00', 'turn_highlight')
        # Put hex under units visualy
        self.canvas.tag_raise(unit.id, hex)
        for field in unit.pos.neighbor_fields:
            for u in self.units:
                if u.pos == field:
                    self.canvas.tag_raise(u.id, hex)
        

        # Highlight the walkable tiles 
        self.unit_walked_fields = set()
        self.unit_walked_fields.add(unit.pos) # make unit pos highlighted for estetics
        self.pathfinding(unit, random.choice(unit.pos.neighbor_fields), unit.current_actions)
        for field in self.unit_walked_fields:
            self.canvas.itemconfig(field.id, fill=field.walkable_color)
        self.canvas.delete('unit_path')


    def combat(self): # Main Gameloop in the arena
        self.draw_turn_order()
        self.mouse_hold = unit = self.current_turn_order[0]
        unit.current_actions = unit.actions

        self.refresh_unit(unit)

       
    def pathfinding(self, unit, end, actions):
        if unit.pos == end:
            self.canvas.delete('unit_path')

        self.backtracking_result = [0] * 100

        self._backtracking(unit.pos, end, actions, [])

        if self.backtracking_result != [0] * 100:
            self.canvas.delete('unit_path')
            for i in range(len(self.backtracking_result) - 1):
                x0, y0, x1, y1 = self.backtracking_result[i].x, self.backtracking_result[i].y, self.backtracking_result[i+1].x, self.backtracking_result[i+1].y
                self.canvas.create_line(x0,y0, x1,y1, width=7, fill='#2a362d', tags='unit_path')
        
        else:
            self.canvas.delete('unit_path')


    # Internal function for calculating the path
    def _backtracking(self, pos, end,  actions, road):
        road.append(pos)

        if pos == end and len(road) < len(self.backtracking_result):
            self.backtracking_result = road.copy()

        if len(road) <= actions:
            for field in pos.neighbor_fields:
                if field not in road and field.occupied == None: # Check if unit can go that far and field is not occupied
                    if field not in self.unit_walked_fields:
                        self.unit_walked_fields.add(field)
                    self._backtracking(field, end, actions, road)

        road.pop()
       

    class Field: # One Hexagon 
        def __init__(self, canvas: tk.Canvas, row: int, col: int):
            # Variables Setup
            self.canvas = canvas
            self.occupied = None
            self.neighbor_fields = set()
            self.x = None
            self.y = None
            self.row = row
            self.col = col
            self.id = None
            self.color = None
            self.walkable_color = None

        def draw(self, side_lenght, x, y, offset):
            self.color = color = 'green'

            # Changed color of the field when units can walk on it
            if color == 'green':
                self.walkable_color = '#4aed75'

            self.x = x = x + offset
            self.y = y
            angle = 2 * math.pi / 6
            points = []

            if self.occupied == True:
                color = '#bd8a86'

            for pdx in range(6):
                _angle = angle * pdx + math.pi/6
                _x = x + math.cos(_angle) * side_lenght
                _y = y + math.sin(_angle) * side_lenght
                points.append((_x, _y))
            self.id = self.canvas.create_polygon(*points, width=2, outline='black', fill=color, tags='field')

        
    class Unit: # One creature on the battlefield
        def __init__(self, id_num, unit_name, player=1):
            self.player = player
            self.canvas: tk.Canvas = None 
            self.canvas_id = None
            self.pos = None
            self.delayed = False
            

            player_colors = ['blue', 'red', 'green', 'yellow']

            self.player_color = player_colors[player -1]

            units = {'Warrior': {'stats': {'health': 100, 
                                    'damage': 50, 
                                    'actions':7,
                                    'attack_range':1},
                            'color': 'red'},
                    'Tank': { 'stats':{'health':200, 
                                    'damage':25, 
                                    'actions':5,
                                    'attack_range':1},
                            'color': 'gray'},
                    'Archer': {'stats':{'health': 75, 
                                        'damage':40, 
                                        'actions': 4,
                                        'attack_range':8},
                               'color': 'blue'}, }

            self.name = unit_name
            self.health = self.current_health = units[unit_name]['stats']['health']
            self.damage = units[unit_name]['stats']['damage']
            self.attack_range = units[unit_name]['stats']['attack_range']
            self.actions = self.current_actions = units[unit_name]['stats']['actions']

            self.color = units[unit_name]['color']

            self.id = f'{self.name}_{id_num}'

        def draw(self, canvas: tk.Canvas, image):
            x, y = self.pos.x, self.pos.y
            self.canvas = canvas
            self.canvas_id = []

            # Creature
            self.canvas_id = self.canvas_id = canvas.create_image(x,y+30, anchor='s', image= image, tags=('unit', self.id))

            # Binds left click to see more info
            self.canvas.tag_bind(self.canvas_id, '<3>', func=self.draw_stats, add=True)

            # Healthbar
            offset = 60 - (60 * ((self.current_health) / self.health))
            canvas.create_rectangle(x-30,y-7 +40,x+30,y+7 +40, tags=self.id)
            canvas.create_rectangle(x-30,y-7 +40,x+30 - offset,y+7 +40, width=0, fill='#1ff02a', tags=self.id)
            canvas.create_text(x,y+40, text=f'{self.current_health}/{self.health}', font=("Helvetica", 12), tags=self.id)

        def draw_stats(self, event):
            x,y = event.x, event.y
            self.canvas.create_rectangle(x, y, x+150, y+150, fill='light blue', tags='temporary')
            self.canvas.create_text(x+75, y+20, text=self.name, font=("Helvetica", 15), tags='temporary')
            self.canvas.create_text(x+75, y+60, text=f'HP: {self.current_health}\{self.health}', font=("Helvetica", 15), tags='temporary')
            self.canvas.create_text(x+75, y+80, text=f'DMG: {self.damage}', font=("Helvetica", 15), tags='temporary')
            self.canvas.create_text(x+75, y+100, text=f'ACTIONS: {self.actions}', font=("Helvetica", 15), tags='temporary')

                

if __name__ == "__main__":
    root = tk.Tk()
    root.title('Poggers')
    root.config(cursor='arrow')


    arena = Arena(root)

    