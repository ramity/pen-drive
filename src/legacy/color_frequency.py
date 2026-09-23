import cv2
import numpy as np
import sys

def color_frequency(img_path):
    """
    Calculate color frequency in an image.
    """
    # Read image
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    if img is None:
        print(f"Error: Could not read image at {img_path}")
        return None

    # Get image dimensions
    height, width, _ = img.shape
    print(f"Image dimensions: {width}x{height}")

    # Count pixels for each color
    colors = {}
    for y in range(height):
        for x in range(width):
            color = tuple(img[y, x])
            colors[color] = colors.get(color, 0) + 1

    # Sort colors by frequency (descending)
    sorted_colors = sorted(colors.items(), key=lambda x: x[1], reverse=True)

    # Print color frequencies
    for color, count in sorted_colors:
        print(f"Color #{int(color[2]):02x}{int(color[1]):02x}{int(color[0]):02x} : {count}")

    return sorted_colors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python color_frequency.py <image_path>")
        sys.exit(1)

    img_path = sys.argv[1]
    color_frequency(img_path)
