import sys
import os 
from utils.gpu import GPUgo
from utils.mutil import TaskAssignment
import click
from loguru import logger 


@click.command()
@click.option('-t', help = "firstwaitTime", type = int, default = 15)
@click.option('-k', required=False, type = int, help='kill all process on device, enter -1 to kill all tasks on all GPUs')
@click.option('-f', help="the script for assignment", type=click.STRING)
@click.option('-n', help="task quantitative limitation on each device ", type=int, default = 3)
@click.option('-d', help="select specific device to run tasks", type=str)
@click.option('-l', help="safe free memory level to ensure no overflow", type=float, default = 0.9)




def main( t,k,f,n,d,l):


    gpugo = GPUgo()
    gpugo.GetGpuInfo()
    GPUs = gpugo.GPUs

    if d:
        GPUs = [gpu for  gpu in GPUs if gpu.GPU_index in d.split(',')]

 
    if not f:
        gpugo.ShowmyGpuInfo()
    if f:
        if k > len(GPUs)-1:
            print(f"There is no gpu device's index  {k}")
            return

        assert os.path.isfile(f), "Please enter correct script path!"
        logger.add("./file.log",format="{time} {message}", filter="", level="INFO") 
      
        assign = TaskAssignment(task_path = f,  perdetask = n, firstwaitTime = t, maxdeiveoccmem = l)
        assign.run()

    
    if k != None : 
        if k > len(GPUs):
            print(f"there is no device {k} Plase check!")
            
        if k == -1:
            [gpu.kill_process() for gpu in GPUs]
            
        else:
            GPUs[k].kill_process()
            return
    else:    
        gpugo.MyGpuInfo()



if __name__ == '__main__':
    main()