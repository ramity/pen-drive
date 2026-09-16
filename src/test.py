import math
import random
import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# Pure-Python Galois Field GF(2^8) & Robust Reed-Solomon Engine
# =====================================================================

class GaloisField256:
    """Galois Field GF(2^8) math implementation using generator polynomial 0x11D."""
    def __init__(self, prim=0x11D):
        self.exp = [0] * 512
        self.log = [0] * 256
        x = 1
        for i in range(255):
            self.exp[i] = x
            self.log[x] = i
            x <<= 1
            if x & 0x100:
                x ^= prim
        for i in range(255, 512):
            self.exp[i] = self.exp[i - 255]

    def add(self, x, y):
        return x ^ y

    def sub(self, x, y):
        return x ^ y

    def mul(self, x, y):
        if x == 0 or y == 0:
            return 0
        return self.exp[self.log[x] + self.log[y]]

    def div(self, x, y):
        if y == 0:
            raise ZeroDivisionError()
        if x == 0:
            return 0
        return self.exp[(self.log[x] + 255 - self.log[y]) % 255]

    def pow(self, x, power):
        return self.exp[(self.log[x] * power) % 255]

    def poly_mul(self, p1, p2):
        r = [0] * (len(p1) + len(p2) - 1)
        for j, c2 in enumerate(p2):
            for i, c1 in enumerate(p1):
                r[i + j] ^= self.mul(c1, c2)
        return r

    def poly_eval(self, poly, x):
        y = 0
        for coef in poly:
            y = self.mul(y, x) ^ coef
        return y


class ReedSolomon:
    """Configurable Reed-Solomon encoder/decoder over GF(2^8)."""
    def __init__(self, n_sym=16, gf=None):
        self.n_sym = n_sym  # Parity bytes per block
        self.gf = gf or GaloisField256()
        self.gen = self._generator_poly(n_sym)

    def _generator_poly(self, n):
        g = [1]
        for i in range(n):
            g = self.gf.poly_mul(g, [1, self.gf.pow(2, i)])
        return g

    def encode(self, msg: bytes) -> bytes:
        if len(msg) + self.n_sym > 255:
            raise ValueError(f"Block size {len(msg) + self.n_sym} exceeds GF(256) limit of 255")

        msg_list = list(msg)
        padded = msg_list + [0] * self.n_sym
        for i in range(len(msg_list)):
            coef = padded[i]
            if coef != 0:
                for j in range(len(self.gen)):
                    padded[i + j] ^= self.gf.mul(self.gen[j], coef)
        return bytes(msg_list + padded[len(msg_list):])

    def decode(self, msg: bytes) -> bytes:
        msg_list = list(msg)

        # 1. Calculate Syndromes
        synd = [0] * self.n_sym
        has_error = False
        for i in range(self.n_sym):
            val = self.gf.poly_eval(msg_list, self.gf.pow(2, i))
            synd[i] = val
            if val != 0:
                has_error = True

        if not has_error:
            return bytes(msg_list[:-self.n_sym])

        # 2. Berlekamp-Massey Algorithm to find Error Locator Polynomial
        C = [1]
        B = [1]
        L = 0
        m = 1
        b = 1

        for N in range(self.n_sym):
            d = synd[N]
            for i in range(1, L + 1):
                d ^= self.gf.mul(C[i], synd[N - i])

            if d == 0:
                m += 1
            else:
                T = list(C)
                coef = self.gf.div(d, b)

                # C(x) = C(x) ^ (coef * x^m * B(x))
                padded_B = [0] * m + [self.gf.mul(coef, x) for x in B]
                max_len = max(len(C), len(padded_B))
                C = [0] * max_len
                for idx, val in enumerate(T):
                    C[idx] ^= val
                for idx, val in enumerate(padded_B):
                    C[idx] ^= val

                if 2 * L <= N:
                    L = N + 1 - L
                    B = T
                    b = d
                    m = 1
                else:
                    m += 1

        # 3. Chien Search to find Error Roots
        err_pos = []
        for i in range(len(msg_list)):
            # Evaluate error locator at X_i^-1
            x_inv = self.gf.pow(2, 255 - i)
            if self.gf.poly_eval(C, x_inv) == 0:
                err_pos.append(len(msg_list) - 1 - i)

        if len(err_pos) != L or len(err_pos) * 2 > self.n_sym:
            raise ValueError("Uncorrectable: Too many errors in block")

        # 4. Error Evaluator Polynomial (Omega)
        synd_rev = list(reversed(synd))
        omega = self.gf.poly_mul(synd, C)[:self.n_sym]

        # 5. Forney Algorithm to calculate Error Magnitudes
        C_prime = [C[i] for i in range(1, len(C), 2)]  # Formal Derivative of C(x)

        for pos in err_pos:
            Xi = self.gf.pow(2, pos)
            Xi_inv = self.gf.pow(2, 255 - pos)

            y = self.gf.poly_eval(omega, Xi_inv)
            z = self.gf.poly_eval(C_prime, self.gf.pow(Xi_inv, 2))

            magnitude = self.gf.div(self.gf.mul(Xi, y), z)
            msg_list[len(msg_list) - 1 - pos] ^= magnitude

        return bytes(msg_list[:-self.n_sym])


# =====================================================================
# Main Image Storage Pipeline & Verification
# =====================================================================

plot_width = 181
plot_height = 206
cell_width = 0.6
cell_height = 0.2
stroke_size = 0.2
colors = 8  # Set power of 2 for clean bit-packing (3 bits/cell)

RS_N_SYM = 16
RS_BLOCK_SIZE = 255
RS_PAYLOAD_SIZE = RS_BLOCK_SIZE - RS_N_SYM

cell_x = int(plot_width // cell_width)
cell_y = int(plot_height // cell_height)
cell_x_resolution = int(round(cell_width / stroke_size))
cell_y_resolution = int(round(cell_height / stroke_size))
total_cells = cell_x * cell_y

bits_per_cell = int(math.log2(colors))
total_capacity_bytes = (total_cells * bits_per_cell) // 8

# Compute payload capacity accounting for RS parity overhead
num_blocks = total_capacity_bytes // RS_BLOCK_SIZE
usable_payload_bytes = num_blocks * RS_PAYLOAD_SIZE

print(f"Total cells: {total_cells}")
print(f"Total Storage Capacity: {total_capacity_bytes} bytes ({num_blocks} blocks)")
print(f"Usable Payload Capacity: {usable_payload_bytes} bytes")

# 1. Generate Raw Data
raw_payload = bytes([random.randint(0, 255) for _ in range(usable_payload_bytes)])

# 2. Encode Data using Reed-Solomon
rs = ReedSolomon(n_sym=RS_N_SYM)
encoded_stream = bytearray()
for i in range(0, len(raw_payload), RS_PAYLOAD_SIZE):
    chunk = raw_payload[i : i + RS_PAYLOAD_SIZE]
    encoded_stream.extend(rs.encode(chunk))

# 3. Render Byte Stream onto Image Grid
step = 4096 // colors
pallet = [color for color in range(0, 4096, step)]
color_to_val = {color: idx for idx, color in enumerate(pallet)}

image_width = int(plot_width // stroke_size)
image_height = int(plot_height // stroke_size)
image = np.zeros((image_height, image_width), dtype=np.uint16)

# Pack bytes into dynamic bit reader
bit_str = "".join([f"{b:08b}" for b in encoded_stream])

cell_idx = 0
for y in range(cell_y):
    start_y = y * cell_y_resolution
    for x in range(cell_x):
        start_x = x * cell_x_resolution
        
        bit_idx = cell_idx * bits_per_cell
        if bit_idx + bits_per_cell <= len(bit_str):
            val = int(bit_str[bit_idx : bit_idx + bits_per_cell], 2)
        else:
            val = 0

        image[start_y : start_y + cell_y_resolution, start_x : start_x + cell_x_resolution] = pallet[val]
        cell_idx += 1

plt.imsave("image.png", image, cmap="gray")
print("Image rendered and saved.")

# =====================================================================
# Image Damage, Readback, and Error Correction Verification
# =====================================================================

# 4. Simulate Noise/Corrupt directly on the Image Array (Optical Media Damage)
corrupted_image = image.copy()

# Add random noise spots across cells (up to 8 byte-errors per block)
max_errors_per_block = RS_N_SYM // 2
cells_per_block = (RS_BLOCK_SIZE * 8) // bits_per_cell

for block_i in range(num_blocks):
    errors_to_inject = random.randint(1, max_errors_per_block)
    for _ in range(errors_to_inject):
        cell_offset = random.randint(0, cells_per_block - 1)
        target_cell = block_i * cells_per_block + cell_offset

        cy = target_cell // cell_x
        cx = target_cell % cell_x

        if cy < cell_y:
            sy = cy * cell_y_resolution
            sx = cx * cell_x_resolution
            # Corrupt cell color in image matrix
            corrupted_image[sy : sy + cell_y_resolution, sx : sx + cell_x_resolution] = random.choice(pallet)

plt.imsave("corrupted_image.png", corrupted_image, cmap="gray")
print("Injected random cell noise onto the image surface.")

# 5. Extract Byte Stream back from Image Pixels
extracted_bits = []
for y in range(cell_y):
    start_y = y * cell_y_resolution
    for x in range(cell_x):
        start_x = x * cell_x_resolution
        # Read first pixel of cell
        cell_color = corrupted_image[start_y, start_x]

        # Quantize to closest palette color value
        val = color_to_val.get(cell_color, 0)
        extracted_bits.append(f"{val:0{bits_per_cell}b}")

extracted_bit_str = "".join(extracted_bits)
extracted_bytes = bytearray(
    int(extracted_bit_str[i : i + 8], 2)
    for i in range(0, num_blocks * RS_BLOCK_SIZE * 8, 8)
)

# 6. Decode Extracted Byte Stream back to Raw Payload
decoded_payload = bytearray()
errors_corrected = 0

for i in range(0, len(extracted_bytes), RS_BLOCK_SIZE):
    block = extracted_bytes[i : i + RS_BLOCK_SIZE]
    try:
        decoded_block = rs.decode(block)
        decoded_payload.extend(decoded_block)
        errors_corrected += 1
    except ValueError as e:
        print(f"Block at byte offset {i} uncorrectable: {e}")

# Verification Check
if decoded_payload == raw_payload:
    print(f"\nSUCCESS: Recovered 100% of the payload ({len(raw_payload)} bytes) from damaged optical image!")
else:
    print("\nFAILURE: Mismatch between raw and decoded payload.")
