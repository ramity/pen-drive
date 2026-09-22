import cv2

# This script assumes k-means has already been run and we have the channel masks.
# Now we have channel_color_1 - channel_color_10 where each file is a black and white image.
# The idea now is to reconstruct the original WryCode image using the channel masks.

# Load the original crop.png image
crop = cv2.imread("crop.png")

# Load the channel masks
channel_masks = []
for i in range(10):
    channel_masks.append(cv2.imread(f"channel_color_{i+1}.png"))

# 