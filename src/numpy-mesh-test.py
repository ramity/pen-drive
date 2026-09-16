import numpy as np
from stl import mesh

# Define vertices and faces of a cube
vertices = np.array([
    [-1, -1, -1], [+1, -1, -1], [+1, +1, -1], [-1, +1, -1],
    [-1, -1, +1], [+1, -1, +1], [+1, +1, +1], [-1, +1, +1],
])
faces = np.array([
    [0, 3, 1], [1, 3, 2], [0, 4, 7], [0, 7, 3],
    [4, 5, 6], [4, 6, 7], [5, 1, 2], [5, 2, 6],
    [2, 3, 6], [3, 7, 6], [0, 1, 5], [0, 5, 4],
])

cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        cube.vectors[i][j] = vertices[f[j], :]

cube.save('cube.stl')