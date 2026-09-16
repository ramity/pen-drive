#!/usr/bin/env bash

# ==============================================================================
# Physical Off-Network Chroma-Matrix Storage Density Calculator
# ==============================================================================

# --- CONFIGURABLE PARAMETERS ---
TOTAL_COLORS=9            # Number of distinct pen colors (excluding empty background)
CELL_SIZE_MM="0.20"       # Total grid cell pitch/spacing (X and Y) in mm
STROKE_WIDTH_MM="0.20"    # Physical pen line width in mm
STROKE_LENGTH_MM="0.20"   # Lateral movement stroke length in mm
GRID_WIDTH_MM="181.0"     # Printable plot width in mm
GRID_HEIGHT_MM="206.0"    # Printable plot height in mm
ECC_PERCENT=0             # Error Correction Code (Reed-Solomon) overhead %
MARGIN_BORDER_MM="0.0"    # Reserved edge margin for alignment targets/legend
PEN_CHANGE_TIME_SEC=25    # Estimated time in seconds to swap and zero a pen
PRUSA_SPEED_MMS=30        # Plotting speed in mm/s

# ==============================================================================
# CALCULATION ENGINE
# ==============================================================================

# Calculate printable area after subtracting border margins
USEABLE_WIDTH=$(awk "BEGIN {print $GRID_WIDTH_MM - (2 * $MARGIN_BORDER_MM)}")
USEABLE_HEIGHT=$(awk "BEGIN {print $GRID_HEIGHT_MM - (2 * $MARGIN_BORDER_MM)}")

# Grid dimensions in terms of cells
COLUMNS=$(awk "BEGIN {print int($USEABLE_WIDTH / $CELL_SIZE_MM)}")
ROWS=$(awk "BEGIN {print int($USEABLE_HEIGHT / $CELL_SIZE_MM)}")
TOTAL_CELLS=$((COLUMNS * ROWS))

# Number of symbols/states = TOTAL_COLORS + 1 (Empty state '0')
TOTAL_STATES=$((TOTAL_COLORS + 1))

# Bits per cell: log2(TOTAL_STATES)
BITS_PER_CELL=$(awk "BEGIN {print log($TOTAL_STATES)/log(2)}")

# Total raw information capacity
TOTAL_RAW_BITS=$(awk "BEGIN {print $TOTAL_CELLS * $BITS_PER_CELL}")
TOTAL_RAW_BYTES=$(awk "BEGIN {print $TOTAL_RAW_BITS / 8}")
TOTAL_RAW_KB=$(awk "BEGIN {print $TOTAL_RAW_BYTES / 1024}")

# Usable data capacity after Error Correction Code (ECC)
USABLE_BYTES=$(awk "BEGIN {print $TOTAL_RAW_BYTES * (1 - ($ECC_PERCENT / 100))}")
USABLE_KB=$(awk "BEGIN {print $USABLE_BYTES / 1024}")

# Plotting time estimates
TOTAL_PEN_CHANGE_TIME_SEC=$((TOTAL_COLORS * PEN_CHANGE_TIME_SEC))

# Estimate stroke distance: Assuming ~80% cell occupancy across non-empty states
ACTIVE_CELLS=$(awk "BEGIN {print int($TOTAL_CELLS * ($TOTAL_COLORS / $TOTAL_STATES))}")
TOTAL_DRAW_DIST_MM=$(awk "BEGIN {print $ACTIVE_CELLS * $STROKE_LENGTH_MM}")
DRAW_TIME_SEC=$(awk "BEGIN {print $TOTAL_DRAW_DIST_MM / $PRUSA_SPEED_MMS}")
TOTAL_PRINT_TIME_MIN=$(awk "BEGIN {print ($DRAW_TIME_SEC + $TOTAL_PEN_CHANGE_TIME_SEC) / 60}")

# Minimum required scanner optical DPI to resolve stroke
MIN_SCAN_DPI=$(awk "BEGIN {print int((25.4 / $STROKE_WIDTH_MM) * 3)}")

# ==============================================================================
# OUTPUT REPORT
# ==============================================================================

echo "========================================================================"
echo "         CHROMA-MATRIX PHYSICAL STORAGE DENSITY ANALYSIS               "
echo "========================================================================"
echo "Grid Geometry:"
echo "  - Total Plot Area        : ${GRID_WIDTH_MM} mm x ${GRID_HEIGHT_MM} mm"
echo "  - Usable Grid Area       : ${USEABLE_WIDTH} mm x ${USEABLE_HEIGHT} mm (after ${MARGIN_BORDER_MM}mm margins)"
echo "  - Cell Pitch / Spacing   : ${CELL_SIZE_MM} mm x ${CELL_SIZE_MM} mm"
echo "  - Stroke Size            : ${STROKE_WIDTH_MM} mm width x ${STROKE_LENGTH_MM} mm length"
echo "  - Grid Array Matrix      : ${COLUMNS} cols x ${ROWS} rows (${TOTAL_CELLS} total cells)"
echo ""
echo "Encoding & Symbolics:"
echo "  - Color Count            : ${TOTAL_COLORS} pens (+ 1 background/empty state)"
echo "  - Encoding Base          : Base-${TOTAL_STATES}"
echo "  - Information Density    : $(printf "%.3f" "$BITS_PER_CELL") bits / cell"
echo "  - ECC Overhead           : ${ECC_PERCENT}%"
echo ""
echo "Data Storage Capacity:"
echo "  - Raw Bit Capacity       : $(printf "%.0f" "$TOTAL_RAW_BITS") bits"
echo "  - Raw Byte Capacity      : $(printf "%.2f" "$TOTAL_RAW_KB") KB ($(printf "%.0f" "$TOTAL_RAW_BYTES") Bytes)"
echo "  - USABLE DATA CAPACITY   : $(printf "%.2f" "$USABLE_KB") KB ($(printf "%.0f" "$USABLE_BYTES") Bytes)"
echo ""
echo "Execution & Scan Requirements:"
echo "  - Active Pen Strokes     : ~${ACTIVE_CELLS} strokes"
echo "  - Total Travel Distance  : $(printf "%.1f" "$TOTAL_DRAW_DIST_MM") mm"
echo "  - Total Pen Swap Overhead: ${TOTAL_PEN_CHANGE_TIME_SEC} seconds (${TOTAL_COLORS} manual swaps)"
echo "  - Est. Total Plot Time   : $(printf "%.2f" "$TOTAL_PRINT_TIME_MIN") minutes"
echo "  - Min Scanner Resolution : ${MIN_SCAN_DPI} DPI (Recommended: 1200 DPI)"
echo "========================================================================"