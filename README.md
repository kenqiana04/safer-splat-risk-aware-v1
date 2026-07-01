<!-- # SAFER-Splat
### [Project Page](https://chengine.github.io/safersplat) | [Paper (ICRA)]() | [Paper (arXiv)]() | [Data](https://drive.google.com/drive/u/1/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh)
[SAFER-Splat: Simultaneous Action Filtering and Environment Reconstruction]()  
 [Timothy Chen](https://msl.stanford.edu/people/timchen)\*<sup>1</sup>,
 [Aiden Swann](https://msl.stanford.edu/people/timchen)\*<sup>1</sup>,
 [Javier Yu](https://msl.stanford.edu/people/timchen)\*<sup>1</sup>,
 [Ola Shorinwa](https://www.its.caltech.edu/~pculbert/)\*<sup>1</sup>,
 [Riku Murai](https://www.its.caltech.edu/~pculbert/)\*<sup>2</sup>,
 [Monroe Kennedy III](https://www.its.caltech.edu/~pculbert/)\*<sup>1</sup>,
 [Mac Schwager](https://web.stanford.edu/~schwager/)\*<sup>1</sup>,
 <sup>1</sup>Stanford, <sup>2</sup>Princeton, <sup>3</sup>Imperial College London
in IEEE Transactions on Robotics (2024)

<img src='imgs/title.png'/> -->

<p align="center">

  <h1 align="center"><img src="imgs/icon.svg" width="25"> SAFER-Splat: Simultaneous Action Filtering and Environment Reconstruction</h1>
  <p align="center"> 
    <a href="https://msl.stanford.edu/people/timchen"><strong>Timothy Chen</strong><sup>1</sup></a>
    ·
    <a href="https://aidenswann.com/"><strong>Aiden Swann</strong><sup>1</sup></a>
    ·
    <a href="https://msl.stanford.edu/people/javieryu"><strong>Javier Yu</strong><sup>1</sup></a>
    ·
    <a href="https://msl.stanford.edu/people/olashorinwa"><strong>Ola Shorinwa</strong><sup>1</sup></a>
    ·
    <a href="https://rmurai.co.uk/"><strong>Riku Murai</strong><sup>2</sup></a>
    ·
    <a href="https://me.stanford.edu/people/monroe-kennedy"><strong>Monroe Kennedy III</strong><sup>1</sup></a>
    ·
    <a href="https://web.stanford.edu/~schwager/"><strong>Mac Schwager</strong><sup>1</sup></a>
  </p>
  <p align="center"><strong><sup>1</sup>Stanford University</strong></p>
  <p align="center"><strong><sup>2</sup>Imperial College London</strong></p>
  <h2 align="center">Accepted ICRA 2025</h2>
  <h3 align="center"><a href="https://chengine.github.io/safer-splat"> Project Page</a> | <a href=>Paper</a> | <a href= "https://www.arxiv.org/abs/2409.09868">arXiv</a> | <a href="https://drive.google.com/drive/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh?usp=sharing">Data</a></h3>
  <div align="center"></div>
</p>
<p align="center">
  <a href="">
    <img src="imgs/title.png" width="80%">
  </a>
</p>
<h3 align="center">
SAFER-Splat (Simultaneous Action Filtering and Environment Reconstruction) is a real-time, scalable, and minimally invasive action filter, based on control barrier functions, for safe robotic navigation in a detailed map constructed at runtime using Gaussian Splatting.
</h3>

## About
We propose a novel Control Barrier Function (CBF) that not only induces safety with respect to all Gaussian primitives in the scene, but when synthesized into a controller, is capable of processing hundreds of thousands of Gaussians while maintaining a minimal memory footprint and operating at 15 Hz during online Splat training. Of the total compute time, a small fraction of it consumes GPU resources, enabling uninterrupted training. The safety layer is minimally invasive, correcting robot actions only when they are unsafe. To showcase the safety filter, we also introduce SplatBridge, an open-source software package built with ROS for real-time GSplat mapping for robots. We demonstrate the safety and robustness of our pipeline first in simulation, where our method is 20-50x faster, safer, and less conservative than competing methods based on neural radiance fields. Further, we demonstrate simultaneous GSplat mapping and safety filtering on a drone hardware platform using only on-board perception. We verify that under teleoperation a human pilot cannot invoke a collision.

## Features
1. We provide ROS 2 nodes in `ros` branch. This includes SplatBridge and the CBF functions.
2. You can now view the Gaussian Splat and the CBF trajectories in viser. See **Visualizing the paths** section.

## TODOs
1. Provide interactive Colab notebook that allows users to interface with the safety layer on a trained Splat.

## Dependencies
This repository is built off of [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio/tree/main). Please first follow the installation instructions there before installing any of the dependencies specifically for this repository. Once you have Nerfstudio installed in your Conda environment, install the following dependencies in that environment.

* [CLARABEL](https://github.com/oxfordcontrol/Clarabel.rs). This library is for solving the quadratic program.

### Dependencies (Simplified)
Our codebase is tested with Python 3.10, Nerfstudio 1.1.5, viser 0.2.7, Clarabel 0.10.0, Numpy 1.26.4, PyTorch 2.1.2, and CUDA 11.8. You can get up and running the quickest following the following commands:

```
conda create -n safersplat python=3.10
conda activate safersplat
pip install --upgrade pip

git clone https://github.com/chengine/safer-splat.git
cd safer-splat

pip install torch==2.1.2+cu118 torchvision==0.16.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
conda install -c "nvidia/label/cuda-11.8.0" cuda-toolkit
pip install nerfstudio==1.1.5
pip install -r requirements.txt
```

## Datasets
Our datasets are hosted on a [Google Drive](https://drive.google.com/drive/folders/1xSu7bFW8OBRd9YHfz3LzdBx7pDjUHEPh?usp=sharing). The scenes used in the paper are `flightgate`, `statues`,  `stonehenge`, `adirondacks`. The training data is in the `data` folder, while the model parameters are in `outputs`. You can drag and drop these folders into your working directory.

Here's an example:
```
SAFER-Splat
├── data                                                                                                       
│   └── flight
│       └── images
│       └── transforms.json                                                                                  
│                                                                                               
├──outputs                                                                                                                                                      
│   └── flight                                                                                                  
│       └── splatfacto                                                                                                                             
│           └── 2024-09-12_172434                                                                               
│               └── nerfstudio_models
|               └── config.yml
|               └── dataparser_transforms.json # This file contains the transform that transforms from "Data" frame to "Nerfstudio" frame (which is typically a unit box)
├── run.py
```

## Running SAFER-Splat
After the dependencies and the data is setup, run
```
python run.py
```

The most important thing is to ensure that the path in GSplatLoader is pointing to the right model location.

### Variants
The variants for the distance can be changed. ```run.py``` allows you to change the distance type within the script.

### Visualizing the paths
Run the ```visualize.py```, setting your scene name and method type properly so that the script correctly extracts the Gaussian Splatting model and the saved trajectory data (that was created through ```run.py```). This script will launch viser and load your trajectories into the visualizer. If you run into issues where viser informs you that ```add_gaussian_splats``` does not exist, this means you have an outdated version of viser (likely one that came packaged with Nerfstudio) and will need to upgrade [viser](https://github.com/nerfstudio-project/viser). Afterwards, navigate to the specified port in the browser to visualize the trajectories and the ellipsoidal representation of the Gaussian Splat. 

## Generating your own scenes
To use your own datasets, simply train a Nerfstudio `splatfacto` model and follow the folder structure as illustrated above. If your images contain pixels that are transparent like in the case of synthetic scenes (i.e. the alpha value is 0), it is recommended to use the `instant-ngp-data` flag (e.g. `ns-train splatfacto --data {DATA} instant-ngp-data`) rather than `blender-data` or the default.

## Citation
If you found SAFER-Splat useful, consider citing us! Thanks!
```
@misc{chen2024safersplatcontrolbarrierfunction,
      title={SAFER-Splat: A Control Barrier Function for Safe Navigation with Online Gaussian Splatting Maps}, 
      author={Timothy Chen and Aiden Swann and Javier Yu and Ola Shorinwa and Riku Murai and Monroe Kennedy III au2 and Mac Schwager},
      year={2024},
      eprint={2409.09868},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2409.09868}, 
}
```
