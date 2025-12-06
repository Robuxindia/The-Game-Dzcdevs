"""Minimal Ursina demo: load texture atlas and create a few voxel cubes using Ursina's Entity system.
Requires `ursina` package.
"""
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os

app = Ursina()

# try load atlas
atlas_path = os.path.join('textures','blocks.png')
if not os.path.exists(atlas_path):
    print('Ursina demo: textures/blocks.png bulunamadı. Lütfen atlası yerleştirin.')

# simple block entity using atlas as texture
class Block(Entity):
    def __init__(self, position=(0,0,0), texture=None):
        super().__init__(model='cube', texture=texture, position=position, scale=1)

# create ground and some blocks
if os.path.exists(atlas_path):
    tex = load_texture(atlas_path)
else:
    tex = None

for x in range(-4,5):
    for z in range(-4,5):
        Block(position=(x,-1,z), texture=tex)

Block(position=(0,0,3), texture=tex)
Block(position=(1,0,3), texture=tex)
Block(position=(0,1,3), texture=tex)

player = FirstPersonController()

app.run()

