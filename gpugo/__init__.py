import sys
import os 
import click
from loguru import logger 
from .gpu import GPUgo
from .mutil import TaskAssignment


@click.command()
@click.option('-k', required=False, type = int, help='kill all process on device, enter -1 to kill all tasks on all GPUs')
@click.option('-f', help="the script for assignment", type=click.STRING)
@click.option('-n', help="the max number of task on each device", type=int, default= 4 )
@click.option('-t', help=" the estimation time for the first execution", type=int, default= 15 )




def main( k,f, n,t):
    gpugo = GPUgo()
    gpugo.GetGpuInfo()
    GPUs = gpugo.GPUs
     

    if not f:
        gpugo.ShowmyGpuInfo()
    if f:
        assert os.path.isfile(f), "Please enter correct script path!"
        logger.add("./file.log",format="{time} {message}", filter="", level="INFO")
        assign = TaskAssignment(task_path = f, perdetask= n ,firstwaitTime=t)
        assign.run()
    if k != None : 
        if k > len(GPUs)-1:
            print(f"There is no gpu device's index  {k}")
            return

        if k == -1:
            [gpu.kill_process() for gpu in GPUs]
            
        else:
            GPUs[k].kill_process()
            return
    else:    
        gpugo.MyGpuInfo()



if __name__ == '__main__':
    main()