import random
import matplotlib.pyplot as plt
import numpy as np
from stl import mesh

# Configuration Parameters
# plot_width, plot_height = 181, 206
plot_width, plot_height = 50, 50
cell_width, cell_height, cell_depth = 0.4, 0.4, 0.1
stroke_size = 0.2
colors = 10

# Geometry definition
base_vertices = np.array(
    [
        [0, 0, 0],
        [cell_width, 0, 0],
        [cell_width, cell_height, 0],
        [0, cell_height, 0],
        [0, 0, cell_depth],
        [cell_width, 0, cell_depth],
        [cell_width, cell_height, cell_depth],
        [0, cell_height, cell_depth],
    ]
)

cell_faces = np.array(
    [
        [0, 3, 1],
        [1, 3, 2],  # Bottom (-Z)
        [0, 4, 7],
        [0, 7, 3],  # Front (-Y)
        [4, 5, 6],
        [4, 6, 7],  # Top (+Z)
        [5, 1, 2],  # Right (+X)
        [5, 2, 6],
        [2, 3, 6],  # Back (+Y)
        [3, 7, 6],
        [0, 1, 5],  # Left (-X)
        [0, 5, 4],
    ]
)

# Grid setup
cell_x = int(plot_width // cell_width)
cell_y = int(plot_height // cell_height)
cell_x_res = int(round(cell_width / stroke_size))
cell_y_res = int(round(cell_height / stroke_size))
total_cells = cell_x * cell_y
storage_in_bits = total_cells * colors
storage_in_bytes = storage_in_bits / 8
storage_in_kb = storage_in_bytes / 1024
print(f"Total cells: {total_cells}")
print(f"Storage in KB: {storage_in_kb}")
print(f"Cell Resolution: {cell_x_res} x {cell_y_res}")

# Palette setup
step = 4096 // colors
palette = list(range(0, 4096, step))

# Generate grid state directly (1 value per cell)
cell_grid = np.random.choice(palette, size=(cell_y, cell_x))

# Generate raster preview image
image = np.repeat(np.repeat(cell_grid, cell_y_res, axis=0), cell_x_res, axis=1)
plt.imsave("image.png", image, cmap="gray")

# Generate 3D grid coordinate offsets
x_coords = np.arange(cell_x) * cell_width
y_coords = (cell_y - 1 - np.arange(cell_y)) * cell_height
grid_x, grid_y = np.meshgrid(x_coords, y_coords)
offsets = np.stack(
    [grid_x.ravel(), grid_y.ravel(), np.zeros(cell_x * cell_y)], axis=-1
)

flat_grid = cell_grid.ravel()

# Process each color STL using vectorized construction
for color in palette:
    match_mask = flat_grid == color
    color_offsets = offsets[match_mask]

    print(color_offsets)

    num_cells = len(color_offsets)

    if num_cells == 0:
        continue

    # Compute target triangle coordinates: [num_cells, 12_faces, 3_verts, 3_coords]
    cell_verts = base_vertices + color_offsets[:, np.newaxis, :]
    face_vectors = cell_verts[:, cell_faces]

    # Reshape into a single flat list of triangles
    all_triangles = face_vectors.reshape(-1, 3, 3)

    # Instantiate STL mesh directly
    color_mesh = mesh.Mesh(
        np.zeros(all_triangles.shape[0], dtype=mesh.Mesh.dtype)
    )
    color_mesh.vectors = all_triangles

    print(f"Exporting color {color} ({num_cells} cells)...")
    color_mesh.save(f"{color}.stl")
