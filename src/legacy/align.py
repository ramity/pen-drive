import cv2
import numpy as np

# 1. Load images with verification
img_to_align = cv2.imread("created.jpg")
reference_img = cv2.imread("source.jpg")

if img_to_align is None or reference_img is None:
    raise FileNotFoundError("Could not load one or both input images.")

gray_align = cv2.cvtColor(img_to_align, cv2.COLOR_BGR2GRAY)
gray_ref = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)

# 2. Detect ORB keypoints and descriptors
orb = cv2.ORB_create(nfeatures=2000)
kp1, des1 = orb.detectAndCompute(gray_align, None)
kp2, des2 = orb.detectAndCompute(gray_ref, None)

if des1 is None or des2 is None:
    raise ValueError("Could not extract descriptors from one or both images.")

# 3. Match descriptors using KNN (K=2) and Lowe's Ratio Test
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
raw_matches = matcher.knnMatch(des1, des2, k=2)

# Filter good matches (ratio threshold typically between 0.7 and 0.8)
good_matches = []
for m_n in raw_matches:
    if len(m_n) == 2:
        m, n = m_n
        if m.distance < 0.85 * n.distance:
            good_matches.append(m)

# 4. Ensure minimum required matches for Homography
if len(good_matches) < 4:
    raise ValueError(f"Not enough valid matches found ({len(good_matches)}/4 required).")

# Extract locations of good matches
pts_align = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
pts_ref = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

# 5. Find Homography with RANSAC
H, mask = cv2.findHomography(pts_align, pts_ref, cv2.RANSAC, 5.0)

if H is None:
    raise RuntimeError("Homography computation failed.")

# 6. Warp image to reference dimensions
height, width = reference_img.shape[:2]
aligned_img = cv2.warpPerspective(img_to_align, H, (width, height))

cv2.imwrite("aligned.jpg", aligned_img)
print("Alignment completed successfully.")