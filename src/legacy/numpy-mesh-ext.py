import numpy as np
from stl import mesh

# 1. Define base geometry dimensions (mm)
width, height, depth = 0.6, 0.2, 0.1

# Define initial vertices centered or relative to origin [0, width], [0, height], [0, depth]
base_vertices = np.array(
    [
        [0, 0, 0],
        [width, 0, 0],
        [width, height, 0],
        [0, height, 0],
        [0, 0, depth],
        [width, 0, depth],
        [width, height, depth],
        [0, height, depth],
    ]
)

# 12 triangles forming the 6 faces of a box
faces = np.array(
    [
        [0, 3, 1],
        [1, 3, 2],  # Bottom (-Z)
        [0, 4, 7],
        [0, 7, 3],  # Front (-Y)
        [4, 5, 6],
        [4, 6, 7],  # Top (+Z)
        [5, 1, 2],
        [5, 2, 6],  # Back (+Y)
        [2, 3, 6],
        [3, 7, 6],  # Right (+X)
        [0, 1, 5],
        [0, 5, 4],  # Left (-X)
    ]
)

# 2. Setup 5x5 Grid parameters
rows, cols = 5, 5
pitch_x, pitch_y = 1.0, 1.0  # Spacing between instances (mm)

num_triangles_per_prism = len(faces)
total_triangles = num_triangles_per_prism * rows * cols

# Create a single mesh array containing all grid instances
grid_mesh = mesh.Mesh(np.zeros(total_triangles, dtype=mesh.Mesh.dtype))

# 3. Populate instances into the grid
tri_index = 0
for r in range(rows):
    for c in range(cols):
        # Calculate offset for this specific grid position
        offset = np.array([c * pitch_x, r * pitch_y, 0.0])
        inst_vertices = base_vertices + offset

        for f in faces:
            for j in range(3):
                grid_mesh.vectors[tri_index][j] = inst_vertices[f[j], :]
            tri_index += 1

# 4. Save combined STL file
grid_mesh.save("prism_grid_5x5.stl")
