import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d, gaussian_filter
from scipy.signal import find_peaks
import numpy as np

def generate_mock_scanned_grid(grid_shape=(10, 10), cell_size=30, noise_level=0.15):
    """Generates a synthetic scanned grid image with bleeding, blur, and noise."""
    np.random.seed(42)
    rows, cols = grid_shape
    
    # 1. Map 10 discrete target palette colors (RGB)
    palette = np.array([
        [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255],
        [0, 255, 255], [128, 0, 0], [0, 128, 0], [0, 0, 128], [128, 128, 0]
    ], dtype=np.float32)
    
    # Assign random colors to grid cells
    grid_indices = np.random.randint(0, 10, size=(rows, cols))
    ideal_grid = palette[grid_indices] # shape: (rows, cols, 3)
    
    # Upsample to image pixel dimensions
    img = np.repeat(np.repeat(ideal_grid, cell_size, axis=0), cell_size, axis=1)
    
    # 2. Simulate scanning artifacts (blur + color bleeding + pixel noise)
    img_scanned = gaussian_filter(img, sigma=(2.5, 2.5, 0)) # Spatial bleed/blur
    noise = np.random.normal(0, noise_level * 255, img.shape)
    img_scanned = np.clip(img_scanned + noise, 0, 255).astype(np.uint8)
    
    return img_scanned, grid_indices

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
    D_smooth = gaussian_filter1d(D_profile, sigma=1.5)
    
    # 2. Estimate periodicity
    estimated_pitch = estimate_grid_period(D_smooth)
    min_dist = int(estimated_pitch * 0.75) if estimated_pitch else 10
    
    # 3. Peak detection with minimum distance constraint
    peaks, _ = find_peaks(D_smooth, distance=min_dist, prominence=np.std(D_smooth) * 0.5)
    return peaks, D_smooth

# --- EXECUTION ---
# 1. Create simulated scan
img, ground_truth = generate_mock_scanned_grid(grid_shape=(10, 10), cell_size=32)

# 2. Compute 1D distance arrays (Column-wise and Row-wise)
D_c, D_r = compute_distance_profiles(img)

# 3. Detect column & row boundaries
x_boundaries, Dc_smooth = extract_boundaries(D_c)
y_boundaries, Dr_smooth = extract_boundaries(D_r)

# 4. Infer center points of detected grid cells
x_centers = ((x_boundaries[:-1] + x_boundaries[1:]) / 2).astype(int)
y_centers = ((y_boundaries[:-1] + y_boundaries[1:]) / 2).astype(int)

# --- VISUALIZATION ---
fig, axes = plt.subplots(2, 2, figsize=(10, 10), gridspec_kw={'height_ratios': [1, 3], 'width_ratios': [3, 1]})

# Top: Column distance array & peaks
axes[0, 0].plot(D_c, color='gray', alpha=0.5, label='Raw D_c')
axes[0, 0].plot(Dc_smooth, color='red', label='Smoothed D_c')
axes[0, 0].vlines(x_boundaries, 0, max(D_c), color='blue', linestyle='--', label='Boundaries')
axes[0, 0].set_title("Column-wise Distance Profile")
axes[0, 0].set_xlim(0, img.shape[1])
axes[0, 0].legend(loc='upper right', fontsize='small')

# Main: Scanned image with overlaid detected grid
axes[1, 0].imshow(img)
for x in x_boundaries:
    axes[1, 0].axvline(x, color='cyan', linewidth=1.5, linestyle='--')
for y in y_boundaries:
    axes[1, 0].axhline(y, color='cyan', linewidth=1.5, linestyle='--')

# Plot sampled center sampling locations
grid_x, grid_y = np.meshgrid(x_centers, y_centers)
axes[1, 0].scatter(grid_x, grid_y, color='yellow', s=15, zorder=5, label='Sample Center')
axes[1, 0].set_title("Detected Grid Boundaries & Sample Centers")
axes[1, 0].legend(loc='lower left', fontsize='small')

# Right: Row distance array & peaks
axes[1, 1].plot(Dr_smooth, range(len(Dr_smooth)), color='red')
axes[1, 1].hlines(y_boundaries, 0, max(D_r), color='blue', linestyle='--')
axes[1, 1].set_ylim(img.shape[0], 0)
axes[1, 1].set_title("Row-wise Profile")

axes[0, 1].axis('off')
plt.tight_layout()
plt.show()

print(f"Detected {len(x_boundaries)-1} columns and {len(y_boundaries)-1} rows.")
