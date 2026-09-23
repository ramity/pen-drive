import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d, gaussian_filter
from scipy.signal import find_peaks

plot = cv2.imread("crop.png", cv2.IMREAD_COLOR)

# Variable plot is the scropped subregion of a scanned image.
# The plot itself is effectively a 10 color QR code without sync or localization patterns.
# It is entirely data.
# There are 10 primary colors used in the plot. White being one of them.
# The goal is to localize a grid to the image.
# Let's say we can assume that the image is already prerotated for us so it's properly aligned.

# Let's take a stab at a possible value strategy:
# Read in the image row by row
# previous_row_pixel_sum = np.zeros(3)
# previous_distance = 0
# for y, row in enumerate(plot):
#     pixel_sum = np.zeros(3)
#     for pixel in row:
#         pixel_sum += pixel / len(row)
#     # calculate the distance between pixel_sum and previous_pixel_sum
#     distance = np.sqrt(np.sum((pixel_sum - previous_row_pixel_sum) ** 2))
#     print(y, pixel_sum, previous_row_pixel_sum, distance, previous_distance, distance - previous_distance)
#     previous_row_pixel_sum = pixel_sum
#     previous_distance = distance

# # Read the plot column-wise
# previous_column_pixel_sum = np.zeros(3)
# previous_distance = 0
# for x, row in enumerate(plot[:,[2,1,0],:]):
#     pixel_sum = np.zeros(3)
#     for pixel in row:
#         pixel_sum += pixel / len(row)
#     # calculate the distance between pixel_sum and previous_pixel_sum
#     distance = np.sqrt(np.sum((pixel_sum - previous_column_pixel_sum) ** 2))
#     print(x, pixel_sum, previous_column_pixel_sum, distance, previous_distance, distance - previous_distance)
#     previous_column_pixel_sum = pixel_sum
#     previous_distance = distance

def compute_distance_profiles(img):
    """
    Computes 1D distance profile arrays:
    Distance between average pixel value and previous average pixel value.
    """
    # Convert to float for accurate difference math
    img_f = img.astype(np.float32)

    # Profile along columns (collapse rows via mean -> shape: (width, 3))
    col_means = np.mean(img_f, axis=0)
    # Profile along rows (collapse columns via mean -> shape: (height, 3))
    row_means = np.mean(img_f, axis=1)

    # Euclidean distance between consecutive spatial step averages
    D_c = np.linalg.norm(col_means[1:] - col_means[:-1], axis=1)
    D_r = np.linalg.norm(row_means[1:] - row_means[:-1], axis=1)

    # Pad first element to maintain 1:1 pixel coordinate indexing
    D_c = np.pad(D_c, (1, 0), mode='edge')
    D_r = np.pad(D_r, (1, 0), mode='edge')

    return D_c, D_r

D_c, D_r = compute_distance_profiles(plot)
# print(D_c)
# print(D_r)

def estimate_grid_period(D_profile):
    """Estimates dominant grid cell pitch (periodicity) via Autocorrelation."""
    # Center the signal
    norm_profile = D_profile - np.mean(D_profile)
    autocorr = np.correlate(norm_profile, norm_profile, mode='full')
    autocorr = autocorr[len(autocorr)//2:] # Keep positive lags

    # Find peaks in autocorrelation, skipping lag=0
    peaks, _ = find_peaks(autocorr[5:], distance=5)
    if len(peaks) > 0:
        return peaks[0] + 5 # Adjust index offset
    return None

def extract_boundaries(D_profile):
    """Extracts pixel indices representing cell boundary transitions."""
    # 1. Smooth signal to ignore high-frequency pixel scan noise
    D_smooth = gaussian_filter1d(D_profile, sigma=1)

    # 2. Estimate periodicity
    estimated_pitch = estimate_grid_period(D_smooth)
    min_dist = int(estimated_pitch * 0.75) if estimated_pitch else 10

    # 3. Peak detection with minimum distance constraint
    peaks, _ = find_peaks(D_smooth, distance=min_dist, prominence=np.std(D_smooth) * 0.5)
    return peaks, D_smooth

c_peaks, c_d_smooth = extract_boundaries(D_c)
r_peaks, r_d_smooth = extract_boundaries(D_r)

print(c_peaks)
print(r_peaks)
# print(c_d_smooth)
# print(r_d_smooth)

# now calculate the most common difference between consecutive values of c_peaks and r_peaks
c_offset = c_peaks[1:] - c_peaks[:-1]
r_offset = r_peaks[1:] - r_peaks[:-1]

# get the mode of c_offset and r_offset
c_mode = np.argmax(np.bincount(c_offset))
r_mode = np.argmax(np.bincount(r_offset))

print(c_mode)
print(r_mode)

x_offset = c_peaks[0]
y_offset = r_peaks[0]

# draw grid using x_offset and y_offset and spacing of c_mode and r_mode
# for x in range(x_offset, len(plot[0]), c_mode):
#     cv2.line(plot, (x, 0), (x, len(plot)), (0, 255, 0), 1)
# for y in range(y_offset, len(plot), r_mode):
#     cv2.line(plot, (0, y), (len(plot[0]), y), (0, 255, 0), 1)

# draw lines
test = plot.copy()
for i in c_peaks:
    cv2.line(test, (i, 0), (i, len(plot)), (0, 0, 0), 1)
for i in r_peaks:
    cv2.line(test, (0, i), (len(plot[0]), i), (0, 0, 0), 1)

cv2.imwrite("test.png", test)

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

def known_weighted_color_distance(color):
    """
    Calculates the weighted distance between a color and a set of known colors.
    Because the set of known colors are not evenly spaced from each other in RGB space, 
    we need to find a weighted distance that takes into account the distance between
    the known colors themselves.
    """

    known_colors_array = np.array(list(known_colors.values()))

    # Compute distances from the input color to all known colors
    distances = np.array([color_distance(known_color, color) for known_color in known_colors_array])

    # Create a weighting matrix based on distances between known colors
    # This creates a "map" of color relationships
    n_known = len(known_colors_array)
    weights = np.ones((n_known, n_known))
    for i in range(n_known):
        for j in range(i + 1, n_known):
            # Use a kernel that assigns higher weight to closer pairs
            weight = np.exp(-color_distance(known_colors_array[i], known_colors_array[j]) / 100.0)
            weights[i, j] = weights[j, i] = weight

    # Apply weights to the distances
    # This effectively "warps" the color space so nearby known colors pull the estimate
    weighted_distances = np.dot(weights, distances)

    # Find the known color with the minimum weighted distance
    closest_known_index = np.argmin(weighted_distances)

    return known_colors_array[closest_known_index]

def color_distance(color1, color2):
    """Calculate Euclidean distance between two RGB colors."""
    return np.sqrt(np.sum((np.array(color1, dtype=float) - np.array(color2, dtype=float)) ** 2))

# Now that we have a rough idea of where the pixels to extract actually are, let's iterate back through the plot
# and store average value within the provided [x, y] to [x + c_mode, y + r_mode].
extracted = np.zeros((len(r_peaks) - 1, len(c_peaks) - 1, 3), dtype=np.uint8)
for y_idx, y in enumerate(range(len(r_peaks) - 1)):
    for x_idx, x in enumerate(range(len(c_peaks) - 1)):
        x_start = c_peaks[x_idx]
        x_end = c_peaks[x_idx + 1]
        y_start = r_peaks[y_idx]
        y_end = r_peaks[y_idx + 1]

        # get the subregion of the plot
        cell_pixels = plot[y_start:y_end, x_start:x_end]
        cell_pixels = cell_pixels.reshape(-1, 3)

        # Closest known color approach:
        # closest_color = None
        # min_dist = float('inf')
        # for known_color, known_color_rgb in known_colors.items():
        #     dist = color_distance(np.mean(cell_pixels, axis=0), known_color_rgb)
        #     if dist < min_dist:
        #         min_dist = dist
        #         closest_color = known_color_rgb
        # extracted[y_idx, x_idx] = closest_color

        # Closest known weighted color distance approach:
        # Calculate the color distance between all pixels in the cell and all known colors.
        # For each pixel of the cell_pixels subregion, calculate the closest known color using the weighted_color_distance function, then return the most frequently selected known color.
        selected_colors = []
        for pixel in cell_pixels:
            selected_colors.append(known_weighted_color_distance(pixel))
        unique, counts = np.unique(selected_colors, axis=0, return_counts=True)
        most_frequent_color = unique[np.argmax(counts)]
        extracted[y_idx, x_idx] = most_frequent_color

        # Most frequent color approach:
        # unique, counts = np.unique(cell_pixels, axis=0, return_counts=True)
        # most_frequent_color = unique[np.argmax(counts)]
        # extracted[y_idx, x_idx] = most_frequent_color

        # Mean color approach:
        # extracted[y_idx, x_idx] = np.mean(cell_pixels, axis=0)

        # Simple center approach:
        # just take the color of the pixel at the center of the cell
        # extracted[y_idx, x_idx] = cell_pixels[len(cell_pixels) // 2]

        # Simple center, known colors approach:
        # take the center pixel, and cross reference the list of known colors
        # center_pixel = cell_pixels[len(cell_pixels) // 2]
        # closest_color = None
        # min_dist = float('inf')
        # for known_color, known_color_rgb in known_colors.items():
        #     dist = color_distance(center_pixel, known_color_rgb)
        #     if dist < min_dist:
        #         min_dist = dist
        #         closest_color = known_color_rgb
        # extracted[y_idx, x_idx] = closest_color

        # Sampling, known colors approach:
        # Sample N pixels within the extracted cell and cross reference the average color with list of known colors

        # The weighted known color distance approach:
        # Considers that the set of known colors are not evenly distributed in RGB space.
        # It works by calculating the distance between all pixels in the cell and all known colors.
        # Then it creates a weight matrix based on the distances between the cell and all known colors.
        # Finally it applies the weights to the distances and finds the known color with the minimum weighted distance.
        # estimated_colors = []
        # for pixel in cell_pixels:
        #     estimated_colors.append(known_weighted_color_distance(pixel))
        # extracted[y_idx, x_idx] = np.unique(estimated_colors, axis=0, return_counts=True)[0][np.argmax(np.unique(estimated_colors, axis=0, return_counts=True)[1])]

    cv2.imwrite("test2.png", extracted)
