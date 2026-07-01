import os
import time
from pathlib import Path
from splat.gsplat_utils import GSplatLoader
import torch
import numpy as np
import trimesh
import json
import viser
import viser.transforms as tf
import matplotlib as mpl

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def as_mesh(scene_or_mesh):
    """
    Convert a possible scene to a mesh.

    If conversion occurs, the returned mesh has only vertex and face data.
    """
    if isinstance(scene_or_mesh, trimesh.Scene):
        if len(scene_or_mesh.geometry) == 0:
            mesh = None  # empty scene
        else:
            # we lose texture information here
            mesh = trimesh.util.concatenate(
                tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in scene_or_mesh.geometry.values()))
    else:
        assert(isinstance(mesh, trimesh.Trimesh))
        mesh = scene_or_mesh
    return mesh

### ------------------- ###

### PARAMETERS###
# NOTE: THIS REQUIRES CHANGING TO THE SCENE YOU WANT TO VISUALIZE
scene_name = 'stonehenge'      # statues, stonehenge, old_union, flight. If custom scene, specify path to gsplat config file and trajectory data            
method = 'ball-to-ellipsoid'   # ball-to-ellipsoid, ball-to-ball-squared, ball-to-pt-squared, mahalanobis, ball-to-ball

try:
    if scene_name == 'statues':
        path_to_gsplat = Path('outputs/statues/splatfacto/2024-09-11_095852/config.yml')

    elif scene_name == 'stonehenge':
        path_to_gsplat = Path('outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml')

    elif scene_name == 'old_union':
        path_to_gsplat = Path('outputs/old_union2/splatfacto/2024-09-02_151414/config.yml')

    elif scene_name == 'flight':
        path_to_gsplat = Path('outputs/flight/splatfacto/2024-09-12_172434/config.yml')
    else:
        # If you want a custom scene, you need to specify the path to the gsplat config file and the trajectory data.
        # NOTE:!!! Put your custom scene filepath here...
        raise NotImplementedError
except:
    raise ValueError("Scene or data not found")

traj_filepath = f'trajs/{scene_name}_{method}.json'

bounds = None       # If you want to apply a bounding box, specify it here. Otherwise, set to None. If set, bounds[:, 0] = [min_x, min_y, min_z], bounds[:, 1] = [max_x, max_y, max_z].
rotation = tf.SO3.from_x_radians(0.0).wxyz      # identity rotation. NOTE: If your trajectories are not in the nerfstudio frame (which the scene is), you may have to apply a transformation

### ------------------- ###
gsplat = GSplatLoader(path_to_gsplat, device)

server = viser.ViserServer()

### ------------------- ###
# Only visualize the gsplat within some bounding box set by bounds
if bounds is not None:
    mask = torch.all((gsplat.means - bounds[:, 0] >= 0) & (bounds[:, 1] - gsplat.means >= 0), dim=-1)
else:
    mask = torch.ones(gsplat.means.shape[0], dtype=torch.bool, device=device)

means = gsplat.means[mask]
covs = gsplat.covs[mask]
colors = gsplat.colors[mask]
opacities = gsplat.opacities[mask]

# Add splat to the scene
# NOTE!!! You may have to upgrade viser to the latest version to use this function. If you have the base viser version that comes intsalled
# with nerfstudio, you will likely have to upgrade it. Upgrading viser will not break nerfstudio.
server.scene.add_gaussian_splats(
    name="/splats",
    centers= means.cpu().numpy(),
    covariances= covs.cpu().numpy(),
    rgbs= colors.cpu().numpy(),
    opacities= opacities.cpu().numpy(),
    wxyz=rotation,
)

### ------------------- ###

os.makedirs('assets', exist_ok=True)

# Will save the ellipsoids to a file
if not os.path.exists(f"assets/{scene_name}.obj"):
    gsplat.save_mesh(f"assets/{scene_name}.obj", bounds=bounds, res=4)

# Load the ellipsoidal gsplat
mesh = trimesh.load_mesh(str(Path(__file__).parent / f"assets/{scene_name}.obj"))
assert isinstance(mesh, trimesh.Trimesh)
vertices = mesh.vertices
faces = mesh.faces
print(f"Loaded mesh with {vertices.shape} vertices, {faces.shape} faces")

# Load the ellipsoidal representation
server.scene.add_mesh_simple(
    name="/ellipsoids",
    vertices=vertices,
    faces=faces,
    color=np.array([0.5, 0.5, 0.5]),
    wxyz=rotation,
    opacity=0.5
)

### ------------------- ###

# Load in trajectories
with open(traj_filepath, 'r') as f:
    meta = json.load(f)

datas = meta['total_data']

# Visualize each trajectory and corresponding polytope
for i, data in enumerate(datas):

    # Visualize the trajectory and series of line segments
    traj = np.array(data['traj'])[:, :3]

    points = np.stack([traj[:-1], traj[1:]], axis=1)
    progress = np.linspace(0, 1, len(points))

    # Safety margin color
    cmap = mpl.cm.get_cmap('jet')
    colors = np.array([cmap(prog) for prog in progress])[..., :3]
    colors = colors.reshape(-1, 1, 3)

    # Add trajectory to scene
    server.scene.add_line_segments(
        name=f"/trajs/{i}",
        points=points,
        colors=colors,
        line_width=10,
        wxyz=rotation,
    )
    
while True:
    time.sleep(10.0)