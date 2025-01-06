from PIL import Image
import numpy as np
from stl import mesh
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def generate_faces_for_row(args):
    """Generate faces for a single row of the heightmap."""
    y, cols = args
    row_faces = []
    for x in range(cols - 1):
        # Define the indices of the vertices
        v0 = y * cols + x
        v1 = v0 + 1
        v2 = (y + 1) * cols + x
        v3 = v2 + 1

        # Triangle 1
        row_faces.append((v0, v1, v2))

        # Triangle 2
        row_faces.append((v1, v3, v2))
    return row_faces

def create_mesh_chunk(args):
    """Create a mesh chunk for a subset of faces."""
    chunk_faces, vertices = args
    chunk_mesh = mesh.Mesh(np.zeros(len(chunk_faces), dtype=mesh.Mesh.dtype))
    for i, face in enumerate(chunk_faces):
        for j in range(3):
            chunk_mesh.vectors[i][j] = vertices[face[j], :]
    return chunk_mesh

# Function to convert a heightmap to 3D mesh
def heightmap_to_stl(image_path, output_stl_path, scale=(1, 1, 1), subsample=1):
    """
    Convert a heightmap image to a 3D mesh and save it as an STL file.

    Parameters:
        image_path (str): Path to the input .tif image.
        output_stl_path (str): Path to save the output .stl file.
        scale (tuple): Scaling factors for x, y, and z axes (default: (1, 1, 1)).
        subsample (int): Subsampling factor to reduce resolution (default: 1, no subsampling).
    """
    # Load the image
    img = Image.open(image_path)

    height_data = np.array(img, dtype=np.float32)
    zMin = np.min(height_data)
    zMax = np.max(height_data)
    height_data = height_data - zMin
    print(f'Original Image size {np.shape(height_data)}, z: {zMin}-{zMax}')

    # Subsample the image
    if subsample > 1:
        img = img.resize((img.width // subsample, img.height // subsample), Image.LANCZOS)

    # Get height data as a numpy array
    height_data = np.array(img, dtype=np.float32)
    
    zMin = np.min(height_data)
    zMax = np.max(height_data)
    print(f'Scaled Image size {np.shape(height_data)}, z: {zMin}-{zMax}')
    

    # Scale the height data
    x_scale, y_scale, z_scale = scale
    height_data *= z_scale
    
    # Make the model as thin as possible
    # Adapt this line with a constant if you want to tile multiple prints
    height_data -= zMin

    rows, cols = height_data.shape
    vertices = []

    # Generate vertices for the top surface
    print("Generating vertices...")
    for y in tqdm(range(rows), desc="Rows processed"):
        for x in range(cols):
            vertices.append((x * x_scale, y * y_scale, height_data[y, x]))

    # Add vertices for the bottom face
    for y in range(rows):
        for x in range(cols):
            vertices.append((x * x_scale, y * y_scale, 0))

    # Generate faces for the top surface
    print("Generating faces...")
    with Pool(cpu_count()) as pool:
        rows_faces = list(tqdm(pool.imap(generate_faces_for_row, [(y, cols) for y in range(rows - 1)]), total=rows - 1, desc="Rows processed for faces"))

    faces = [face for row_faces in rows_faces for face in row_faces]

    # Generate faces for the bottom surface (in reverse order)
    offset = rows * cols
    for y in range(rows - 1):
        for x in range(cols - 1):
            v0 = offset + y * cols + x
            v1 = v0 + 1
            v2 = offset + (y + 1) * cols + x
            v3 = v2 + 1

            # Triangle 1
            faces.append((v2, v1, v0))

            # Triangle 2
            faces.append((v3, v1, v2))

    # Generate vertical walls
    for y in range(rows - 1):
        # Left wall
        faces.append((y * cols, (y + 1) * cols, offset + y * cols))
        faces.append(((y + 1) * cols, offset + (y + 1) * cols, offset + y * cols))

        # Right wall
        faces.append((y * cols + cols - 1, offset + y * cols + cols - 1, (y + 1) * cols + cols - 1))
        faces.append(((y + 1) * cols + cols - 1, offset + y * cols + cols - 1, offset + (y + 1) * cols + cols - 1))

    for x in range(cols - 1):
        # Bottom wall
        faces.append((x, x + 1, offset + x))
        faces.append((x + 1, offset + x + 1, offset + x))

        # Top wall
        faces.append(((rows - 1) * cols + x, offset + (rows - 1) * cols + x, (rows - 1) * cols + x + 1))
        faces.append(((rows - 1) * cols + x + 1, offset + (rows - 1) * cols + x, offset + (rows - 1) * cols + x + 1))

    # Create the mesh in parallel
    print("Creating mesh...")
    vertices = np.array(vertices)
    faces = np.array(faces)

    chunk_size = len(faces) // cpu_count()
    chunks = [(faces[i:i + chunk_size], vertices) for i in range(0, len(faces), chunk_size)]

    with Pool(cpu_count()) as pool:
        mesh_chunks = list(tqdm(pool.imap(create_mesh_chunk, chunks), total=len(chunks), desc="Chunks processed"))

    # Combine chunks into a single mesh
    terrain_mesh = mesh.Mesh(np.concatenate([chunk.data for chunk in mesh_chunks]))

    # Save the mesh to an STL file
    print("Saving STL file...")
    terrain_mesh.save(output_stl_path)




if __name__ == "__main__":
    
    # ____________Parameters___________________
    input_tif = r"stitched_imageCrop2.tif"  # Path to your .tif file
    output_stl = "output.stl"  # Desired output .stl file path
    subsample_factor = 4  # Adjust subsampling factor if needed (larger value -> faster, smaller model, less details, should be powers of 2)
    scale_factors = (-0.2 * subsample_factor,0.2 * subsample_factor,1)  # Adjust scaling of model (depends on input data. Example: z-value is in meter but x-y spacing is 20cm => scaleZ = 1/0.2 when subsampling = 1)
    

    heightmap_to_stl(input_tif, output_stl, scale=scale_factors, subsample=subsample_factor)
    print(f"STL file saved to {output_stl}")