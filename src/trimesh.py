import numpy as np
import random
import matplotlib.pyplot as plt
import trimesh

plot_width = 181
plot_height = 206
cell_width = 0.4
cell_height = 0.4
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
total_cells = cell_x * cell_y
storage_in_bits = total_cells * colors
storage_in_bytes = storage_in_bits / 8
storage_in_kb = storage_in_bytes / 1024
print(f"Total cells: {total_cells}")
print(f"Storage in KB: {storage_in_kb}")

# Create a pallet of $colors equally spaced colors from 0x000 to 0xFFF
step = 4096 // colors
pallet = []
for color in range(0, 4096, step):
    pallet.append(int(hex(color), 16))
print(pallet)

# Create an image cell_x width and cell_y height
image = np.zeros((cell_y, cell_x), dtype=np.uint16)

# Iterate through each cell and randomly select a pallet color
for y in range(cell_y):
    for x in range(cell_x):
        image[y, x] = random.choice(pallet)

# save image
plt.imsave("image.jpg", image, cmap="gray")

# now that we have the image, we need to figure out a format such that it can be sliced by prusa slicer to create the image into a plot
# In the past I have used inkscape to convert the image to svg and then used prusa slicer to slice the svg into a plot
# It might be better to create an object via build123d directly

# for each color
for color in pallet:
    print("generating voxels")
    voxels = np.zeros((cell_y, cell_x, int(print_height)), dtype=bool)

    print("creating mask")
    mask = image == color
    voxels[mask] = True
    print("creating mesh")
    mesh = trimesh.voxel.ops.matrix_to_marching_cubes(voxels, pitch=(cell_width, cell_height, 1.0))

    print("exporting")
    mesh.export(f"{color}.stl")


