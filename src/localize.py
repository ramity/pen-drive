import cv2
import numpy as np
import matplotlib.pyplot as plt

# # Load full image and noise sub-image
# full_image = cv2.imread('scan.png', cv2.IMREAD_GRAYSCALE)
# sub_image = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)

# # Substitute sub_image with random noise of the same size
# sub_image = np.random.randint(0, 255, sub_image.shape, dtype=np.uint8)
# cv2.imwrite('noise.png', sub_image)

# # Perform Normalized Cross-Correlation
# res = cv2.matchTemplate(full_image, sub_image, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

# # max_loc contains the (x, y) coordinates of the top-left corner
# h, w = sub_image.shape
# top_left = max_loc
# bottom_right = (top_left[0] + w, top_left[1] + h)

# print(f"Sub-image localized at: {top_left} with correlation score: {max_val:.4f}")

# # Create image with drawn rectangle
# result = cv2.rectangle(full_image, top_left, bottom_right, (0, 255, 0), 2)
# cv2.imwrite('localized.png', result)

full_image = cv2.imread('scan.png', cv2.IMREAD_GRAYSCALE)
color_image = cv2.imread('scan.png', cv2.IMREAD_COLOR)

# full_image is a scan of a sheet of white US letter cardstock. 
# Within roughly the center of the page exists a pen plot that looks like colorful noise. 
# It is actually data.

# Its size and resolution will be dynamic, but it will always be rectangular.

# It may be plotted at a slight angle. Compensate for this.

# The pixels outside the plot region are white. 

# Use some form of scale-invariant normalized cross correlation to find the bounding box of the plot.
# Generate an image of random noise that is the same aspect ratio as the expected plot.

# Maybe try feature detection to get the initial bounding box and then use normalized cross correlation to refine the bounding box.

# 2. Threshold to isolate non-white plot pixels from background
# Background is white (~255), plot noise pixels are darker
_, binary = cv2.threshold(full_image, 240, 255, cv2.THRESH_BINARY_INV)

cv2.imwrite("binary.png", binary)

# 3. Morphological closing to bridge sparse noise points into a solid region
# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
# closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
# cv2.imwrite("closed.png", closed)

# 4. Find contours of the closed plot region
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# cv2.drawContours(full_image, contours, -1, (0, 255, 0), 2)
# cv2.imwrite("contours.png", full_image)

# Select the largest contour (the pen plot area)
largest_contour = max(contours, key=cv2.contourArea)

contour_image = np.zeros_like(full_image)
cv2.drawContours(contour_image, [largest_contour], -1, 255, -1)
cv2.imwrite("largest_contour.png", contour_image)

# 5. Get and draw rotated minimum bounding box of largest_contour
rect = cv2.minAreaRect(largest_contour)
points = np.intp(cv2.boxPoints(rect))
cv2.polylines(full_image, [points], True, (0, 255, 0), 2)
cv2.imwrite("rotated_bounding_box.png", full_image)

# get subregion
min_x, min_y = np.min(points, axis=0)
max_x, max_y = np.max(points, axis=0)

# Ensure integer indices within image bounds
min_x = max(0, int(min_x))
min_y = max(0, int(min_y))
max_x = min(full_image.shape[1], int(max_x))
max_y = min(full_image.shape[0], int(max_y))

subregion = color_image[min_y:max_y, min_x:max_x]
cv2.imwrite("subregion.png", subregion)

# Calculate the color frequency of the subregion

# 2. Define channel names and matching colors for the plot
channels = ('b', 'g', 'r') 

# 3. Loop through each channel and calculate its frequency histogram
plt.figure(figsize=(10, 5))
histograms = []
for i, col in enumerate(channels):
    # cv2.calcHist(images, channels, mask, histSize, ranges)
    hist = cv2.calcHist([subregion], [i], None, [256], [0, 256])
    histograms.append(hist)
    # Plot the frequency line
    plt.plot(hist, color=col)
    plt.xlim([0, 256])

# save plot
plt.savefig("hist.png")
plt.close()

# Calculate the 10 most frequent RGB colors in the subregion image
# Create a list of all RGB values in the subregion
# colors = []
# for y in range(subregion.shape[0]):
#     for x in range(subregion.shape[1]):
#         colors.append(subregion[y, x])

# # Sort the colors by frequency
# colors.sort(key=lambda x: x[0])

# # Get the top 10 most frequent colors by getting the first 10 elements
# most_frequent_colors = colors[:10]

# print(most_frequent_colors)

# # convert the most_frequent_colors into most_frequenct_hex_codes
# most_frequent_hex_codes = []
# for color in most_frequent_colors:
#     hex_code = "#%02x%02x%02x" % (color[0], color[1], color[2])
#     most_frequent_hex_codes.append(hex_code)

# print(most_frequent_hex_codes)

# Given the following hex codes of known colors, extract the pixels from the subregion that are within a threshold of each color

# black  0E0B12
# purple 2C19C2
# blue   002BAB
# cyan   02B6F3
# green  74C707
# pink   FF24AA
# red    F60526
# orange FFB172
# yellow F4D42B
# white  F7EFEF

known_colors = {
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

# for each known color, collapse the colorspace to the given color, making 255 for the pixel at or near that color, and 0 for all other pixels.
for known_color, known_color_rgb in known_colors.items():
    new_image = np.zeros_like(subregion)
    new_image = cv2.inRange(subregion, np.array(known_color_rgb) - 50, np.array(known_color_rgb) + 50)
    cv2.imwrite(f"./masks/{known_color}.png", new_image)

# now create the absolute masks where each mask is loaded and updated by subtracting the other masks from that mask
for known_color, known_color_rgb in known_colors.items():
    new_image = cv2.imread(f"./masks/{known_color}.png")
    for known_color2, known_color_rgb2 in known_colors.items():
        if known_color != known_color2:
            new_image = cv2.subtract(new_image, cv2.imread(f"./masks/{known_color2}.png"))
    cv2.imwrite(f"./masks/{known_color}_absolute.png", new_image)

# now open the image.png file and create the masks/{color}_expected.png files.
# black is 0, white is 255. colors are sorted in the way they are present in known_colors in accending value in the grayscale generated image.png
image = cv2.imread("image.png", cv2.IMREAD_GRAYSCALE)
# get the set of uinique values in the image
image_colors = set(image.flatten())
image_colors = sorted(image_colors)

# combine image_colors and known_colors to enable going from image_colors indexing to known_color name
image_colors_known_colors = dict(zip(image_colors, known_colors.keys()))
for image_color, known_color in image_colors_known_colors.items():
    cv2.imwrite(f"./masks/{known_color}_expected.png", np.where(image == image_color, 255, 0).astype(np.uint8))

def extract_dominant_colors_from_roi(img_bgr, k=10):
    """
    Extracts k dominant colors from an ROI using K-Means in Lab color space.
    """
    # 1. Load image and convert to Lab color space for perceptual accuracy
    img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    # 2. Optional pre-filter on ROI to remove high-frequency noise before clustering
    roi_filtered = cv2.bilateralFilter(img_bgr, d=5, sigmaColor=75, sigmaSpace=75)

    # 3. Reshape ROI pixels into an (N, 3) feature matrix for OpenCV K-Means
    pixels_roi = roi_filtered.reshape((-1, 3)).astype(np.float32)

    # 4. Define K-Means criteria and run clustering on ROI pixels
    # Stops when criteria met: max 100 iterations or accuracy (epsilon) within 1.0
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 1000, 1.0)
    flags = cv2.KMEANS_PP_CENTERS  # Smart centroid initialization

    compactness, labels, centers = cv2.kmeans(
        pixels_roi, k, None, criteria, 10, flags
    )

    # Convert centers back to uint8 (8-bit color depth)
    centers_lab = np.uint8(centers)

    # 5. Quantize the ROI (or full image) using nearest centroid mapping
    # Reshape ROI back to image matrix format using cluster labels
    h, w, _ = img_bgr.shape
    quantized_roi_lab = centers_lab[labels.flatten()].reshape((h, w, 3))

    # 7. Convert Lab centers and quantized image back to BGR for display/saving
    centers_bgr = cv2.cvtColor(centers_lab.reshape(1, k, 3), cv2.COLOR_LAB2BGR).reshape(k, 3)
    quantized_roi_bgr = cv2.cvtColor(quantized_roi_lab, cv2.COLOR_LAB2BGR)

    return centers_bgr, quantized_roi_bgr

# Example usage:
centers_bgr, clean_roi = extract_dominant_colors_from_roi(subregion, k=10)

print("Extracted 10 Clean BGR Colors:")
print(centers_bgr)
print(clean_roi)

cv2.imwrite("clean_roi_bw.png", clean_roi)
