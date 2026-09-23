import cv2
import numpy as np

known_colors = {
    "black": (0x00, 0x00, 0x00), 
    "purple": (0x3A, 0x1F, 0xBC),
    "blue": (0x00, 0x16, 0x9F),
    "cyan": (0x00, 0xAF, 0xF5),
    "green": (0x67, 0xA6, 0x25),
    "pink": (0xFF, 0x2D, 0xBA),
    "red": (0xEF, 0x04, 0x09),
    "orange": (0xF3, 0xB1, 0x76),
    "yellow": (0xFF, 0xD9, 0x33),
    "white": (0xFF, 0xFF, 0xFF),
}

# Image is a cropped subregion of a scan. The scan is a 10 color custom QR code.
image = cv2.imread("crop.png", cv2.IMREAD_COLOR)

# We need to properly identify all 10 colors in the image and identify what each pixel corresponds to.
# We have a set of known_colors. We can use this to identify the colors in the image.
# However, the colors are not all evenly spaced from each other in RGB space.

# How do we map the pixels in the image to the closest known color?
# We can use a weighted distance function to find the closest known color.
# The weight should be based on the distance between the known colors themselves.

def color_distance(color1, color2):
    """
    Calculates the Euclidean distance between two colors in RGB space.
    """
    return np.sqrt(np.sum((np.array(color1, dtype=float) - np.array(color2, dtype=float)) ** 2))

def known_weighted_color_distance(color):
    """
    Calculates the weighted distance between a color and a set of known colors.
    """
    known_colors_array = np.array(list(known_colors.values()))
    distances = np.array([color_distance(known_color, color) for known_color in known_colors_array])
    return distances

def get_closest_known_color(color):
    """
    Gets the closest known color to the given color.
    """
    distances = known_weighted_color_distance(color)
    return list(known_colors.values())[np.argmin(distances)]

# Now that we have a way to identify the colors, we can map the pixels in the image to the closest known color.
for y, row in enumerate(image):
    for x, pixel in enumerate(row):
        image[y, x] = get_closest_known_color(pixel)
