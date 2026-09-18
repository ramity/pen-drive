# Define class Wryre
# Wryre combines the functionality of encoding and decoding wryre images.
# Wryre images are used to store data onto paper by way of pen plotter.

class Wryre:
    def __init__(self):
        self.plot_width: int = 80
        self.plot_height: int = 80
        self.cell_width: float = 0.8
        self.cell_height: float = 0.8
        self.cell_depth: float = 0.1
        self.stroke_size: float = 0.2
        self.colors: int = 10

        self.cell_x = int(self.plot_width // self.cell_width)
        self.cell_y = int(self.plot_height // self.cell_height)
        self.cell_x_res = int(round(self.cell_width / self.stroke_size))
        self.cell_y_res = int(round(self.cell_height / self.stroke_size))

        self.known_colors = {
            "black": (0x0E, 0x0B, 0x12), 
            "purple": (0x2C, 0x19, 0xC2),
            "blue": (0x00, 0x2B, 0xAB),
            "cyan": (0x02, 0xB6, 0xF3),
            "green": (0x74, 0xC7, 0x07),
            "pink": (0xFF, 0x24, 0xAA),
            "red": (0xF6, 0x05, 0x26),
            "orange": (0xFF, 0xB1, 0x72),
            "yellow": (0xF4, 0xD4, 0x2B),
            "white": (0xF7, 0xEF, 0xEF),
        }

    def print_stats(self):
        total_cells = self.cell_x * self.cell_y
        storage_in_bits = total_cells * self.colors
        storage_in_bytes = storage_in_bits / 8
        storage_in_kb = storage_in_bytes / 1024
        print(f"Plot Dimensions: {self.plot_width} x {self.plot_height}")
        print(f"Cell Dimensions: {self.cell_width} x {self.cell_height}")
        print(f"Cell Resolution: {self.cell_x_res} x {self.cell_y_res}")
        print(f"Total Cells: {total_cells}")
        print(f"Number of Colors: {self.colors}")
        print(f"Storage in KB: {storage_in_kb}")

    def generate_palette(self):
        self.palette = []
        step = 4096 // self.colors
        for i in range(0, 4096, step):
            self.palette.append(i)

    def generate_random_image(self):
        cell_grid = np.random.choice(self.palette, size=(self.cell_y, self.cell_x))
        image = np.repeat(np.repeat(cell_grid, self.cell_y_res, axis=0), self.cell_x_res, axis=1)
        return image

    def generate_random_image(self, width: int, height: int):
        new_cell_x = int(width // self.cell_width)
        new_cell_y = int(height // self.cell_height)
        new_cell_x_res = int(round(self.cell_width / self.stroke_size))
        new_cell_y_res = int(round(self.cell_height / self.stroke_size))
        cell_grid = np.random.choice(self.palette, size=(new_cell_y, new_cell_x))
        image = np.repeat(np.repeat(cell_grid, new_cell_y_res, axis=0), new_cell_x_res, axis=1)
        return image

    def convert_image_to_stl_channels(self, image: np.ndarray, stl_directory: str):
        # Geometry definition
        base_vertices = np.array(
            [
                [0, 0, 0],
                [self.cell_width, 0, 0],
                [self.cell_width, self.cell_height, 0],
                [0, self.cell_height, 0],
                [0, 0, self.cell_depth],
                [self.cell_width, 0, self.cell_depth],
                [self.cell_width, self.cell_height, self.cell_depth],
                [0, self.cell_height, self.cell_depth],
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

        # Generate 3D grid coordinate offsets
        x_coords = np.arange(self.cell_x) * self.cell_width
        y_coords = (self.cell_y - 1 - np.arange(self.cell_y)) * self.cell_height
        grid_x, grid_y = np.meshgrid(x_coords, y_coords)
        offsets = np.stack(
            [grid_x.ravel(), grid_y.ravel(), np.zeros(self.cell_x * self.cell_y)], axis=-1
        )

        flat_grid = image.ravel()

        # Process each color STL using vectorized construction
        for color in self.palette:
            match_mask = flat_grid == color
            color_offsets = offsets[match_mask]
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
            color_mesh.save(f"{stl_directory}/{color}.stl")

    def extract_subregion_from_scan(self, scanned_image: np.ndarray):
        _, binary = cv2.threshold(scanned_image, 240, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(largest_contour)
        points = np.intp(cv2.boxPoints(rect))
        # get subregion
        min_x, min_y = np.min(points, axis=0)
        max_x, max_y = np.max(points, axis=0)

        # Ensure integer indices within image bounds
        min_x = max(0, int(min_x))
        min_y = max(0, int(min_y))
        max_x = min(scanned_image.shape[1], int(max_x))
        max_y = min(scanned_image.shape[0], int(max_y))

        subregion = scanned_image[min_y:max_y, min_x:max_x]
        return subregion

    def convert_image_to_channel_masks(self, image: np.ndarray, masks_directory: str):
        # for each known color, collapse the colorspace to the given color, making 255 for the pixel at or near that color, and 0 for all other pixels.
        for known_color, known_color_rgb in self.known_colors.items():
            new_image = np.zeros_like(image)
            new_image = cv2.inRange(image, np.array(known_color_rgb) - 50, np.array(known_color_rgb) + 50)
            cv2.imwrite(f"{masks_directory}/{known_color}.png", new_image)

        # now create the absolute masks where each mask is loaded and updated by subtracting the other masks from that mask
        for known_color, known_color_rgb in self.known_colors.items():
            new_image = cv2.imread(f"{masks_directory}/{known_color}.png")
            for known_color2, known_color_rgb2 in self.known_colors.items():
                if known_color != known_color2:
                    new_image = cv2.subtract(new_image, cv2.imread(f"{masks_directory}/{known_color2}.png"))
            cv2.imwrite(f"{masks_directory}/{known_color}_absolute.png", new_image)

    def validate_channel_masks(self, known_wryre_image: np.ndarray, masks_directory: str):
        output = np.zeros((known_wryre_image.shape[0], known_wryre_image.shape[1], 3), dtype=np.uint8)
        image_colors_known_colors = dict(zip(self.palette, self.known_colors.keys()))

        for color_index, known_color in image_colors_known_colors.items():

            # get the absolute mask
            absolute_mask = cv2.imread(f"{masks_directory}/{known_color}_absolute.png", cv2.IMREAD_GRAYSCALE)
            # then get the corresponding channel from the known_wryre_image
            absolute_image_mask = np.where(known_wryre_image == color_index, 255, 0)

            # compare absolute_mask and absolute_image_mask
            # green when both values match
            output[np.where(absolute_mask == absolute_image_mask)] = (0, 255, 0)
            # red when values do not match
            output[np.where(absolute_mask != absolute_image_mask)] = (0, 0, 255)
            cv2.imwrite(f"{masks_directory}/{known_color}_result.png", output)
