import cv2
import numpy as np

colors = 10

# Given channel_color_1 to channel_color_N of masks, create an array that contains the color index of each pixel that is 255
# We are going to create an output array of shape (height, width) that contains every possible canidate for each pixel

image = cv2.imread("crop.png", cv2.IMREAD_GRAYSCALE)
output = np.zeros((image.shape[0], image.shape[1], colors), dtype=np.uint8)

# Iterate over each color channel array and set the values in output array

for i in range(colors):
    channel_color = cv2.imread(f"channel_color_{i+1}.png", cv2.IMREAD_GRAYSCALE)
    output[channel_color == 255, i] = i

# Now iterate over the output array and create an output image that is pixel 255 for any location that has more than one canidate

output_image = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
output_image[:] = 255
for i in range(image.shape[0]):
    for j in range(image.shape[1]):
        # don't use sum, use count of non-zero elements
        if np.count_nonzero(output[i,j]) == 1:
            output_image[i,j] = 0

# Lastly, save the output to a file for human inspection

cv2.imwrite("canidate_array.png", output_image)
