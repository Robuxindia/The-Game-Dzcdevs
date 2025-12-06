"""Ursina main: simple voxel grid, F5 toggles camera mode, tasks and notifications.
Requires `ursina` installed.
"""
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os
import random

app = Ursina()

# lighting so textures show correct colors
directional_light = DirectionalLight()
directional_light.rotation = (45, -45, 0)
ambient_light = AmbientLight(color=color.rgba(180,180,180,255))
Sky(texture='sky_default')

# state
game_running = False
menu_panel = None
worlds_panel = None
selected_world = None
voxels = []
selected_texture = None
selected_texture_name = None
texture_panel = None
ground_plane = None

# load atlas if present
def find_default_block_texture():
    base = os.path.join('textures','block')
    candidates = ['grass_block_top.png', 'grass_block.png', 'grass.png', 'dirt.png', 'stone.png', 'oak_planks.png']
    if os.path.isdir(base):
        for c in candidates:
            p = os.path.join(base, c)
            if os.path.exists(p):
                return load_texture(p)
        files = [f for f in os.listdir(base) if f.lower().endswith('.png')]
        if files:
            return load_texture(os.path.join(base, random.choice(files)))
    return None

atlas_path = os.path.join('textures','blocks.png')
atlas_tex = load_texture(atlas_path) if os.path.exists(atlas_path) else find_default_block_texture()

# build a small texture cache from textures/block
texture_cache = {}
block_tex_dir = os.path.join('textures','block')
if os.path.isdir(block_tex_dir):
    for f in os.listdir(block_tex_dir):
        if f.lower().endswith('.png'):
            name = os.path.splitext(f)[0]
            try:
                texture_cache[name] = load_texture(os.path.join(block_tex_dir, f))
            except Exception:
                pass

# helper to choose a block texture and return (texture, name)
def choose_texture_for(y):
    # ground layer prefers grass/dirt
    if y == 0:
        for k in ('grass_block_top','grass_block','grass'):
            if k in texture_cache:
                return texture_cache[k], k
        for k in ('dirt', 'coarse_dirt'):
            if k in texture_cache:
                return texture_cache[k], k
    # otherwise pick a random texture (prefer colored ones)
    colored = [(n,t) for n,t in texture_cache.items() if any(c in n for c in ('planks','log','stone','dirt','grass','sand','terracotta'))]
    if colored:
        n,t = random.choice(colored)
        return t, n
    if texture_cache:
        n = random.choice(list(texture_cache.keys()))
        return texture_cache[n], n
    return atlas_tex, None

player = FirstPersonController()
player.visible = False
player.enabled = False

editor_cam = EditorCamera()
editor_cam.disable()

notif_text = Text('', position=(0,0.4), origin=(0,0), scale=2, color=color.azure)

# simple worlds list
WORLD_DENSITY = 0.003
WORLD_SIZE = (48,6,48)
worlds = [{'name':'Demo World','size':WORLD_SIZE}]

# inventory
inventory = {}
inventory_panel = None
hotbar_buttons = []
hotbar_panel = None
selected_hotbar_index = 0

# reverse lookup for texture -> name
texture_to_name = {v: k for k,v in texture_cache.items()}

def spawn_world(world_data):
    # clear existing
    clear_world()
    sx, sy, sz = world_data['size']
    # create a single ground plane to reduce entity count
    global ground_plane
    grass_choices = [k for k in texture_cache.keys() if 'grass' in k]
    if grass_choices:
        gk = grass_choices[0]
        grass_tex = texture_cache[gk]
        ground_plane = Entity(model='plane', scale=(sx,1,sz), texture=grass_tex, collider='box', position=(0,-0.5,0))
        try:
            # reasonable tiling across the plane
            ground_plane.texture_scale = (sx, sz)
        except Exception:
            pass
    else:
        ground_plane = Entity(model='plane', scale=(sx,1,sz), color=color.rgb(70,160,70), collider='box', position=(0,-0.5,0))

    # create sparse above-ground blocks only
    for x in range(sx):
        for y in range(1, sy):
            for z in range(sz):
                if random.random() < WORLD_DENSITY:
                    wx = x - sx//2
                    wy = y - sy//2
                    wz = z - sz//2
                    # ensure integer-aligned y for block centers
                    wy = int(round(wy))
                    # skip spawning at ground level to avoid intersection with ground_plane
                    if wy == 0:
                        continue
                    tex, name = choose_texture_for(y)
                    e = Entity(model='cube', texture=tex, position=(wx, wy, wz), scale=1, collider=None)
                    e.block_name = name
                    e.color = color.white
                    voxels.append(e)
    # position player above the highest block so they spawn standing on the world
    # position player above the plane so they stand on it
    try:
        player.position = (0, 2, 0)
    except Exception:
        player.position = (0, 2, 0)

    # give player some starter blocks if inventory is empty
    if not inventory:
        added = 0
        for name in list(texture_cache.keys()):
            if added >= 5:
                break
            add_to_inventory(name, 8)
            added += 1
    # ensure hotbar reflects starter items (refresh once)
    refresh_hotbar()

    # spawn some simple oak trees (reduced count)
    def try_place_tree(cx, cz):
        # trunk height
        h = random.randint(3,5)
        # check ground at cx,0,cz
        for yy in range(1, h+1):
            pos = (cx, yy, cz)
            e = Entity(model='cube', texture=texture_cache.get('oak_log', atlas_tex), position=pos, scale=1, collider='box')
            e.block_name = 'oak_log' if 'oak_log' in texture_cache else None
            e.color = color.white
            voxels.append(e)
        # small leaves cluster around top (no collider)
        top = h
        for lx in range(-1,2):
            for lz in range(-1,2):
                if abs(lx) + abs(lz) < 3:
                    pos = (cx+lx, top, cz+lz)
                    le = Entity(model='cube', texture=texture_cache.get('oak_leaves', atlas_tex), position=pos, scale=1, collider=None)
                    le.block_name = 'oak_leaves' if 'oak_leaves' in texture_cache else None
                    voxels.append(le)

    # attempt some trees randomly across the map
    for _ in range(max(1, (sx*sz)//600)):
        tx = random.randint(-sx//2, sx//2)
        tz = random.randint(-sz//2, sz//2)
        try_place_tree(tx, tz)


def update():
    # dynamic collider management to reduce physics load
    if not game_running:
        return
    try:
        px, py, pz = int(round(player.x)), int(round(player.y)), int(round(player.z))
    except Exception:
        return
    # keep ground colliders enabled; enable trunk colliders only near player
    radius = 8
    for e in voxels:
        try:
            if e.y == 0:
                if e.collider is None:
                    e.collider = 'box'
                continue
            if getattr(e, 'block_name', None) == 'oak_log':
                if abs(e.x - px) <= radius and abs(e.z - pz) <= radius and abs(e.y - py) <= 4:
                    if e.collider is None:
                        e.collider = 'box'
                else:
                    if e.collider is not None:
                        e.collider = None
            else:
                # non-ground non-trunk blocks keep no collider
                if e.collider is not None:
                    e.collider = None
        except Exception:
            pass

def open_texture_panel():
    global texture_panel
    if texture_panel:
        destroy(texture_panel)
        texture_panel = None
        return
    # hide menu if open
    if menu_panel:
        menu_panel.enabled = False
    # create a grid of texture buttons (limit to first 36 to avoid heavy UI creation)
    buttons = []
    x = -0.35
    y = 0.3
    count = 0
    for name,tex in list(texture_cache.items())[:36]:
        b = Button(text=name, scale=(0.18,0.08), position=(x,y))
        def make_on_click(n,t):
            return lambda: select_texture(n,t)
        b.on_click = make_on_click(name, tex)
        buttons.append(b)
        x += 0.2
        if x > 0.35:
            x = -0.35
            y -= 0.12
        count += 1
    if len(texture_cache) > 36:
        info = Button(text=f"+{len(texture_cache)-36} more...", scale=(0.4,0.06), position=(0, -0.35))
        buttons.append(info)
    texture_panel = WindowPanel(title='Textures (E ile kapat)', content=buttons, popup=True)

def select_texture(name, tex):
    global selected_texture, selected_texture_name, texture_panel
    selected_texture = tex
    selected_texture_name = name
    notif_text.text = f"Seçili: {name}"
    invoke(lambda: setattr(notif_text,'text',''), delay=1.5)


def open_inventory():
    global inventory_panel, hotbar_buttons
    if inventory_panel:
        destroy(inventory_panel)
        inventory_panel = None
        return
    # create a simple hotbar view
    hotbar_buttons = []
    buttons = []
    x = -0.4
    for i, (name,qty) in enumerate(inventory.items()):
        b = Button(text=f"{name} x{qty}", scale=(0.22,0.08), position=(x,0))
        def make_on_click(n):
            return lambda: select_texture(n, texture_cache.get(n))
        b.on_click = make_on_click(name)
        buttons.append(b)
        hotbar_buttons.append(b)
        x += 0.2
    inventory_panel = WindowPanel(title='Envanter (I ile kapat)', content=buttons, popup=True)

def add_to_inventory(name, amount=1):
    inventory[name] = inventory.get(name,0) + amount

def remove_from_inventory(name, amount=1):
    if name not in inventory:
        return False
    inventory[name] -= amount
    if inventory[name] <= 0:
        del inventory[name]
    # caller should refresh hotbar after batch changes
    return True


def refresh_hotbar():
    global hotbar_panel, hotbar_buttons, selected_hotbar_index
    # destroy existing hotbar UI
    if hotbar_panel:
        try:
            destroy(hotbar_panel)
        except Exception:
            pass
    # destroy existing hotbar UI elements
    if hotbar_panel:
        try:
            destroy(hotbar_panel)
        except Exception:
            pass
    for b in hotbar_buttons:
        try:
            destroy(b)
        except Exception:
            pass
    hotbar_buttons = []
    x = -0.45
    i = 0
    # show up to 9 items as individual buttons (no WindowPanel) to avoid a big background
    for name, qty in list(inventory.items())[:9]:
        b = Button(text=f"{name}\nx{qty}", scale=(0.18,0.08), position=(x, -0.45))
        def make_on_click(n, idx=i):
            return lambda: select_hotbar_index(idx, n)
        b.on_click = make_on_click(name)
        hotbar_buttons.append(b)
        x += 0.1
        i += 1
    hotbar_panel = None
    # highlight selected
    if 0 <= selected_hotbar_index < len(hotbar_buttons):
        try:
            hotbar_buttons[selected_hotbar_index].color = color.yellow
        except Exception:
            pass


def select_hotbar_index(idx, name=None):
    global selected_hotbar_index, selected_texture, selected_texture_name
    selected_hotbar_index = idx
    # find the nth item name if name not provided
    if name is None:
        items = list(inventory.keys())
        if idx < len(items):
            name = items[idx]
        else:
            name = None
    if name:
        selected_texture = texture_cache.get(name)
        selected_texture_name = name
        notif_text.text = f"Seçili: {name}"
        invoke(lambda: setattr(notif_text,'text',''), delay=1.2)


def clear_world():
    global voxels
    global ground_plane
    for e in voxels:
        destroy(e)
    voxels = []
    if ground_plane:
        try:
            destroy(ground_plane)
        except Exception:
            pass
        ground_plane = None

def open_menu():
    global menu_panel, worlds_panel, selected_world, game_running
    game_running = False
    # disable player and editor camera
    player.enabled = False
    player.visible = False
    editor_cam.disable()

    if menu_panel:
        destroy(menu_panel)
    if worlds_panel:
        destroy(worlds_panel)

    # Main menu layout: list of buttons
    start_btn = Button(text='Oyuna Gir', color=color.azure, scale=(0.6,0.1))
    worlds_btn = Button(text='Dünyalar', color=color.azure, scale=(0.6,0.1))
    create_btn = Button(text='Dünya Oluştur', color=color.azure, scale=(0.6,0.1))
    exit_btn = Button(text='Çıkış', color=color.red, scale=(0.6,0.1))

    def on_start():
        # spawn selected world or default
        global selected_world, game_running
        if selected_world is None:
            selected_world = worlds[0]
        spawn_world(selected_world)
        # refresh hotbar UI based on inventory
        refresh_hotbar()
        player.enabled = True
        player.visible = True
        if menu_panel:
            menu_panel.enabled = False
        game_running = True

    def on_worlds():
        open_worlds()

    def on_create():
        open_create()

    def on_exit():
        application.quit()

    start_btn.on_click = on_start
    worlds_btn.on_click = on_worlds
    create_btn.on_click = on_create
    exit_btn.on_click = on_exit

    menu_panel = WindowPanel(title='Ana Menü', content=[start_btn, worlds_btn, create_btn, exit_btn], popup=True)

def open_worlds():
    global worlds_panel, selected_world
    # hide main menu while showing worlds
    if menu_panel:
        menu_panel.enabled = False
    if worlds_panel:
        destroy(worlds_panel)
    # create vertically stacked buttons
    buttons = []
    y = 0.2
    for w in worlds:
        b = Button(text=w['name'], scale=(0.8,0.08), position=(0, y))
        def make_on_click(world):
            return lambda: select_world(world)
        b.on_click = make_on_click(w)
        buttons.append(b)
        y -= 0.12
    worlds_panel = WindowPanel(title='Dünyalar', content=buttons, popup=True)

def select_world(world):
    global selected_world
    selected_world = world
    notif_text.text = f"Seçildi: {world['name']}"
    invoke(lambda: setattr(notif_text,'text',''), delay=2)
    if worlds_panel:
        worlds_panel.enabled = False

def open_create():
    # simple create: prompt for name and create default size
    def create_cb(name):
        if not name:
            return
        worlds.append({'name':name,'size':(12,4,12)})
        notif_text.text = f"Dünya oluşturuldu: {name}"
        invoke(lambda: setattr(notif_text,'text',''), delay=2)
        if worlds_panel:
            worlds_panel.enabled = False

    # hide main menu while showing create panel
    if menu_panel:
        menu_panel.enabled = False
    # use InputField inside a panel
    input_field = InputField(default_value='', placeholder='Dünya adı', position=(0,0.06))
    create_btn = Button(text='Oluştur', position=(0,-0.06))
    def on_create_click():
        create_cb(input_field.text)
    create_btn.on_click = on_create_click
    global worlds_panel
    worlds_panel = WindowPanel(title='Dünya Oluştur', content=[input_field, create_btn], popup=True)

def input(key):
    # ESC toggles menu
    if key == 'escape':
        open_menu()
    if key == 'e':
        # light action: if in game and aiming at a block, pick it into inventory; otherwise open inventory (lighter than texture panel)
        if game_running:
            origin = camera.world_position
            direction = camera.forward
            r = raycast(origin, direction, distance=6)
            if r.hit:
                hit = r.entity
                if hit and hit in voxels:
                    name = getattr(hit, 'block_name', None)
                    try:
                        destroy(hit)
                    except Exception:
                        pass
                    if name:
                        add_to_inventory(name, 1)
                        refresh_hotbar()
                        notif_text.text = f'Alındı: {name}'
                        invoke(lambda: setattr(notif_text,'text',''), delay=1.2)
                        return
        # fallback: open inventory (lighter than big texture panel)
        open_inventory()
    if key == 'i':
        open_inventory()
    if key == 'f5' and game_running:
        # toggle camera/editor
        if player.enabled:
            player.enabled = False
            player.visible = True
            editor_cam.enable()
        else:
            editor_cam.disable()
            player.enabled = True
            player.visible = True

    # right click place block when in game
    if key == 'right mouse down' and game_running:
        # place from selected inventory or selected_texture
        if selected_texture_name and inventory.get(selected_texture_name,0) > 0:
            chosen_tex = selected_texture
            chosen_name = selected_texture_name
        elif selected_texture is not None:
            chosen_tex = selected_texture
            chosen_name = texture_to_name.get(selected_texture)
        else:
            chosen_tex = None
            chosen_name = None
        if chosen_tex is None:
            return
        origin = camera.world_position
        direction = camera.forward
        r = raycast(origin, direction, distance=10)
        if r.hit:
            hit = r.entity
            if hit and (hit in voxels or hit == ground_plane):
                pos = r.point + r.normal
                nx = round(pos[0])
                nz = round(pos[2])
                # snap to ground y if placing on ground_plane
                if hit == ground_plane:
                    new_pos = (nx, 0, nz)
                else:
                    new_pos = (nx, round(pos[1]), nz)
                # only place if inventory has the item (if selected_name exists)
                if chosen_name:
                    if inventory.get(chosen_name,0) <= 0:
                        notif_text.text = 'Envanterde yok!'
                        invoke(lambda: setattr(notif_text,'text',''), delay=1.5)
                        return
                    remove_from_inventory(chosen_name,1)
                e = Entity(model='cube', texture=chosen_tex, position=new_pos, scale=1, collider='box')
                e.color = color.white
                voxels.append(e)

    # numeric keys select hotbar 1..9
    if key in [str(i) for i in range(1,10)]:
        idx = int(key) - 1
        select_hotbar_index(idx)

    # left click break block and store in inventory
    if key == 'left mouse down' and game_running:
        origin = camera.world_position
        direction = camera.forward
        r = raycast(origin, direction, distance=10)
        if r.hit:
            hit = r.entity
            if hit and hit in voxels:
                # pick texture name from entity
                name = getattr(hit, 'block_name', None)
                try:
                    destroy(hit)
                except Exception:
                    pass
                if name:
                    add_to_inventory(name,1)
                    notif_text.text = f'Alındı: {name}'
                    invoke(lambda: setattr(notif_text,'text',''), delay=1.2)

open_menu()

app.run()
