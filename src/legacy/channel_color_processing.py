import cv2
import numpy as np
import os
import glob

output = cv2.imread("crop.png", cv2.IMREAD_GRAYSCALE)
output_2 = np.zeros(output.shape, np.uint8fffffffffffffffff)

for filename in glob.glob("channel_color_*"):
    image = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
    contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(output, (x, y), (x+w, y+h), 255, 1)
    cv2.imwrite("channel_color_bounded.png", output)

    # Most common countour size
    sizes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        sizes.append((w, h))
    
    # get most common size
    sizes = np.array(sizes)
    unique, counts = np.unique(sizes, axis=0, return_counts=True)
    most_common = unique[np.argmax(counts)]
    print(most_common)
