 # GPUgo
`GPUgo` is a Python module for getting the GPU status from NVIDA GPUs using `nvidia-smi`.
`GPUgo` would give all your sever's gpu information. Besides, `GPUgo` can assign deep learning tasks to GPU according remaining GPU free memory automatically and run these tasks parallelly without artificial specified
GPU. This will save lots of time. If you are a student with limited GPU resources, it's best for you. 

**Table of Contents**
1. [Backgroud](#background)
1. [Requirements](#requirements)
1. [Installation](#installation)
1. [Usage](#usage)
   1. [show gpu information](#show-gpu-information)
   2. [kill all process on specific device by one command](#kill-all-process-on-specific-device)
   3. [run dl tasks parallelly](#run-dl-tasks-parallelly)
1. [License](#license)


## Background
During the experiment of deep learning, I have to run each task for different backbone many times. At first, I just write them into a script and run it. But this will last a long time even if I have powerful GPU devices. So then I start to think about how to run the experiment faster. Then I write this library GPUgo to execute tasks in parallel. `GPUgo` calculate each task's memory by pre-running in limited time. Then `GPUgo` will assign tasks to diferent GPU device by memory's ascending order. After `GPUgo` get the order, it will start mutil processes to run these task simultaneously.



## Requirements
NVIDIA GPU with latest NVIDIA driver installed.
`gpugo` uses the program `nvidia-smi` to get the GPU status of all available NVIDIA GPUs. `nvidia-smi` should be installed automatically, when you install your NVIDIA driver.

For now, `GPUgo` only support python3.6 or higher on unbuntu. 


Tested on CUDA driver version 418.39 and python 3.7.

## Installation

 1.  Clone this repository:
 ```
 git clone  --recursive https://github.com/wuchangsheng951/gpugo.git
 cd gpugo
 pip install -r requirements.txt
 pip setup.py install
 ```
 2. by pip install
 ```
 pip install gpugo
 ```

## Usage
### show gpu information
show the device's information like  `nvidia-smi`
```
$~ gas
```
Your output should look something like following, depending on your number of GPUs and their current usage:

  ```
  =============================================================================================================================
  device_type device_id utilizationGPU(%)  memoryTotal(MB)  memoryUsed(MB)  memoryFree(MB)  memoryusedPercent(%) task_num
  Quadro P6000         0                 0          24446.0           110.0         24336.0              0.004500        0
      TITAN Xp         1                 0          12196.0             2.0         12194.0              0.000164        0


  -----------------------------------------------------------------------------------------------------------------------------
  there is no task on any device !
  None
  =============================================================================================================================
  ```
### kill all process on specific device by one command

```sh
gas -k [device_id]
```

### run dl tasks in parallel
the script to execute  like this.
```sh
python train_proposed.py --model alexnet --Augmentation True 
python train_proposed.py --model vgg16  --Augmentation True 
python train_proposed.py --model resnet50 --Augmentation True 
python train_proposed.py --model alexnet  --Augmentation False  
python train_proposed.py --model resnet50  --Augmentation False 
python train_proposed.py --model resnet50  --Augmentation False 
```

You're going to execute these tasks in parallel.
```sh
#This method will run several tasks at the same time.
#Make sure your script is under right conda environment
$~ gas -f [script path for script]
```
Parameters

- -f the path for script to execute. Required
- -n the maxinum task number run on each device.
- -t the duration execution time to estimate task's used of memory.

```sh
+-----------------------------------------------------------------------------+
Sat Jul  4 17:04:26 2020       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 418.39       Driver Version: 418.39       CUDA Version: 10.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  Quadro P6000        Off  | 00000000:0A:00.0  On |                  Off |
| 46%   80C    P0   187W / 250W |  16289MiB / 24446MiB |    100%      Default |
+-------------------------------+----------------------+----------------------+
|   1  TITAN Xp            Off  | 00000000:0B:00.0 Off |                  N/A |
| 33%   63C    P2   254W / 250W |   5343MiB / 12196MiB |     99%      Default |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                       GPU Memory |
|  GPU       PID   Type   Process name                             Usage      |
|=============================================================================|
|    0      1155      G   /usr/lib/xorg/Xorg                           107MiB |
|    0     11571      C   python                                      2753MiB |
|    0     11572      C   python                                      2753MiB |
|    0     11574      C   python                                      5331MiB |
|    0     11575      C   python                                      5331MiB |
|    1     11576      C   python                                      5331MiB |
+-----------------------------------------------------------------------------+
```
## LICENSE
See [LICENSE](https://github.com/wuchangsheng951/gpugo/blob/master/LICENSE)