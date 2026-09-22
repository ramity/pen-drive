import cv2
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans


def extract_10_color_channels(image_path, n_colors=10):
    # 1. Load the image and convert to RGB and Lab color spaces
    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Convert to CIE-LAB for perceptually accurate color clustering
    img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    # Reshape pixel array for K-Means: (Height * Width, Channels)
    pixels_lab = img_lab.reshape(-1, 3)

    # 2. Run K-Means Clustering to find the 10 dominant colors
    print("Finding 10 dominant colors using K-Means...")
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels_lab)

    # Reshape labels back to the original image dimensions
    labels_2d = labels.reshape(img_rgb.shape[0], img_rgb.shape[1])

    # Convert cluster centers back from Lab to RGB to view actual color palette
    centers_lab = kmeans.cluster_centers_.astype(np.uint8).reshape(1, n_colors, 3)
    centers_rgb = cv2.cvtColor(centers_lab, cv2.COLOR_LAB2RGB).reshape(
        n_colors, 3
    )

    # 3. Separate each color into its own channel mask
    # Write print output to channel_color_meta.txt
    channels = []
    with open("channel_color_meta.txt", "w") as f:
        f.write("--- Extracted Colors (RGB) ---\n")
        for i in range(n_colors):
            color_rgb = centers_rgb[i]
            f.write(f"Color {i+1}: RGB({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]})\n")

            # Create a channel mask (255 where pixel belongs to this color, 0 elsewhere)
            mask = np.zeros(labels_2d.shape, dtype=np.uint8)
            mask[labels_2d == i] = 255

            # Removes small noise spots from a channel mask
            kernel = np.ones((3, 3), np.uint8)
            cleaned_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            channels.append((color_rgb, cleaned_mask))

            # Optional: Save each channel mask to disk as an image
            cv2.imwrite(f"channel_color_{i+1}.png", cleaned_mask)

    return centers_rgb, channels, img_rgb

# --- Example Usage & Visualization ---
# Run the function on your scanned image:
centers, channels, original_img = extract_10_color_channels("crop.png")
