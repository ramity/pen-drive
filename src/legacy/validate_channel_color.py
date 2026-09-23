import cv2
import numpy as np
import matplotlib.pyplot as plt

colors = 10

# Iterate over each channel_color_N image mask and create a global mask.
# The goal is to make sure that the final image is completely white.

image = cv2.imread("crop.png", cv2.IMREAD_GRAYSCALE)
output = np.zeros(image.shape, np.uint8)
output[:] = 255

for i in range(colors):
    channel_color = cv2.imread(f"channel_color_{i+1}.png", cv2.IMREAD_GRAYSCALE)
    output[channel_color == 255] = 0

cv2.imwrite("global_mask.png", output)

# The global mask is now almost completely black. The zones that are 255 are areas of
# noise that occurs at the boundaries of cells.

# This noise can be used to denote the edges of cells.

# Iterate over the image row wise and take the sum of each row.
# Save the sum to an array.

row_sums = np.sum(output, axis=1)

# Plot the values onto a line graph for human inspection
plt.plot(row_sums)
plt.savefig("row_sums.png")

# Count the number of inflection points and their locations accross row_sums.

def find_inflection_points(arr):
    high_indices = []
    low_indices = []

    # Check elements that have both a left and right neighbor
    for i in range(1, len(arr) - 1):
        # High inflection point (Peak)
        if arr[i] > arr[i-1] and arr[i] > arr[i+1]:
            high_indices.append(i)
        # Low inflection point (Trough)
        elif arr[i] < arr[i-1] and arr[i] < arr[i+1]:
            low_indices.append(i)

    return high_indices, low_indices

high_indices, low_indices = find_inflection_points(row_sums)

print(f"High inflection points: {len(high_indices)}")
print(f"Low inflection points: {len(low_indices)}")

print(f"High inflection points: {high_indices}")
print(f"Low inflection points: {low_indices}")

# Now draw the vertical bars to an image for human inspection

output = cv2.imread("crop.png")
for i in high_indices:
    cv2.line(output, (i, 0), (i, output.shape[0]), (0, 255, 0), 1)
for i in low_indices:
    cv2.line(output, (i, 0), (i, output.shape[0]), (0, 0, 255), 1)

cv2.imwrite("vertical_bars.png", output)
