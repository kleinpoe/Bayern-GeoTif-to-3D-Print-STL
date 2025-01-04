from PIL import Image
import numpy as np
import os


def calculate_edge_difference(edge1, edge2):
    """
    Calculate the sum of absolute differences between two edges.
    """
    return np.sum(np.abs(edge1.astype(dtype=np.float32) - edge2.astype(dtype=np.float32)))


def get_edges(image_array):
    """
    Extract edges (top, bottom, left, right) of an image array.
    """
    top = image_array[0, :]
    bottom = image_array[-1, :]
    left = image_array[:, 0]
    right = image_array[:, -1]
    return {"top": top, "bottom": bottom, "left": left, "right": right}


def find_best_matches(pieces):
    """
    Find the best matching edges between pieces.
    Returns a dictionary of matches and their respective differences.
    """
    matches = {}
    for i, (key1, img1) in enumerate(pieces.items()):
        edges1 = get_edges(img1)
        for j, (key2, img2) in enumerate(pieces.items()):
            if key1 == key2:
                continue
            edges2 = get_edges(img2)
            for side1, edge1 in edges1.items():
                for side2, edge2 in edges2.items():
                    if (side1, side2) in [("top", "bottom"), ("bottom", "top"), ("left", "right"), ("right", "left")]:
                        diff = calculate_edge_difference(edge1, edge2)
                        matches[(key1, key2, side1, side2)] = diff
    return matches


def assemble_image(pieces, matches):
    """
    Assemble the original image from pieces based on matches.
    """
    # Start with a single piece as the top-left corner
    placed_pieces = {list(pieces.keys())[0]: (0, 0)}
    layout = [(0, 0)]
    while len(placed_pieces) < len(pieces):
        for (key1, key2, side1, side2), diff in sorted(matches.items(), key=lambda x: x[1]):
            if key1 in placed_pieces and key2 not in placed_pieces:
                row, col = placed_pieces[key1]
                if side1 == "bottom" and side2 == "top":
                    placed_pieces[key2] = (row + 1, col)
                elif side1 == "top" and side2 == "bottom":
                    placed_pieces[key2] = (row - 1, col)
                elif side1 == "right" and side2 == "left":
                    placed_pieces[key2] = (row, col + 1)
                elif side1 == "left" and side2 == "right":
                    placed_pieces[key2] = (row, col - 1)
                layout.append(placed_pieces[key2])
                break

    # Determine the overall grid dimensions
    min_row = min(r for r, c in layout)
    min_col = min(c for r, c in layout)
    max_row = max(r for r, c in layout)
    max_col = max(c for r, c in layout)
    grid_rows = max_row - min_row + 1
    grid_cols = max_col - min_col + 1

    # Create a blank canvas for the reconstructed image
    piece_height, piece_width = list(pieces.values())[0].shape
    canvas = np.zeros((grid_rows * piece_height, grid_cols * piece_width), dtype=np.float32)

    # Place each piece on the canvas
    for key, (row, col) in placed_pieces.items():
        adjusted_row = row - min_row
        adjusted_col = col - min_col
        start_y = adjusted_row * piece_height
        start_x = adjusted_col * piece_width
        canvas[start_y:start_y + piece_height, start_x:start_x + piece_width] = pieces[key]

    return canvas


def stitch_image(input_folder, output_file):
    """
    Restore the original image from its pieces.
    """
    # Load all pieces
    pieces = {}
    for file in os.listdir(input_folder):
        if file.endswith(".tif"):
            img = Image.open(os.path.join(input_folder, file))
            pieces[file] = np.array(img, dtype=np.float32)

    # Find best matches
    matches = find_best_matches(pieces)

    # Assemble the image
    restored_array = assemble_image(pieces, matches)

    # Save the restored image with proper mode
    restored_img = Image.fromarray(restored_array)
    restored_img.save(output_file)


# _______________Parameters___________________
input_folder = "./SourceImages/"
output_file = "stitched_image.tif"
stitch_image(input_folder, output_file)