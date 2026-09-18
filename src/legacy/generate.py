import numpy as np
import random
import matplotlib.pyplot as plt
from build123d import *
import math

plot_width = 181
plot_height = 206
cell_width = 0.6
cell_height = 0.2
stroke_size = 0.2
colors = 10
print_height = 0.1

# Validate cell sizes
if stroke_size > cell_width or stroke_size > cell_height:
    print("Error: Stroke size must be smaller than cell size")
    exit(1)

# Calculate cell numbers (floor each one since we can't have fractions of cells)
cell_x = int(plot_width // cell_width)
cell_y = int(plot_height // cell_height)
# print(cell_width)
# print(stroke_size)
# print(cell_width / stroke_size)
# print(round(cell_width / stroke_size))
cell_x_resolution = int(round(cell_width / stroke_size))
cell_y_resolution = int(round(cell_height / stroke_size))
total_cells = cell_x * cell_y
storage_in_bits = total_cells * colors
storage_in_bytes = storage_in_bits / 8
storage_in_kb = storage_in_bytes / 1024
print(f"Total cells: {total_cells}")
print(f"Storage in KB: {storage_in_kb}")
print(f"Cell Resolution: {cell_x_resolution} x {cell_y_resolution}")

# Create a pallet of $colors equally spaced colors from 0x000 to 0xFFF
step = 4096 // colors
pallet = []
for color in range(0, 4096, step):
    pallet.append(color)
print(pallet)

# Create an image cell_x width and cell_y height
image_width = int(plot_width // stroke_size)
image_height = int(plot_height // stroke_size)
image = np.zeros((image_height, image_width), dtype=np.uint16)

# Iterate through each cell and randomly select a pallet color
for y in range(cell_y):

    # Calculate pixel y from cell y
    start_y = y * cell_y_resolution

    for x in range(cell_x):

        # Calculate pixel x from cell x
        start_x = x * cell_x_resolution

        # For each pixel in the cell, set the pixel to the chosen color
        image[start_y:start_y + cell_y_resolution, start_x:start_x + cell_x_resolution] = random.choice(pallet)

# save image
plt.imsave("image.png", image, cmap="gray")

import sys
sys.exit()

# now that we have the image, we need to figure out a format such that it can be sliced by prusa slicer to create the image into a plot
# In the past I have used inkscape to convert the image to svg and then used prusa slicer to slice the svg into a plot
# It might be better to create an object via build123d directly

# precompute
half_cell_width = cell_width / 2
half_cell_height = cell_height / 2

# for each color
for color in pallet:
    print("generating locations")

    locations = []

    # for each row
    for y in range(cell_y):
        # for each col
        for x in range(cell_x):
            # if pixel is color then add cell_width x cell_height geometry
            if image[y, x] == color:
                locations.append((x * cell_width, y * cell_height))

    print("building compound")

    pixel = Rectangle(cell_width, cell_height)
    extruded_pixel = extrude(pixel, amount=print_height, clean=False)
    extruded_blocks = [loc * extruded_pixel for loc in Locations(locations)]
    compound = Compound(children=extruded_blocks)

    print("cleaning")
    part = compound.clean()

    # export
    print("exporting")
    part.export_stl(f"{color}.stl")
