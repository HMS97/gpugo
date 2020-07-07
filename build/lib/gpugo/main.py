import sys
import os 
from utils.gpu import GPUgo
from utils.mutil import TaskAssignment
import click
from loguru import logger 


@click.command()
@click.option('-t',is_flag=True )
@click.option('-k', required=False, type = int, help='kill all process on device, enter -1 to kill all tasks on all GPUs')
# @click.argument('file',nargs=-1 ,type=click.File('rb'))
@click.option('-f', help="the script for assignment", type=click.STRING)
@click.option('-n', help="task number on each device ", type=int, defaut = 3)




def main( t,k,f,n):
    gpugo = GPUgo()
    gpugo.GetGpuInfo()
    GPUs = gpugo.GPUs
    logger.add("./file.log",format="{time} {message}", filter="", level="INFO") 

    # logger.info(gpugo.GpuProcessInfo())
    # logger.info(gpugo.Pidmem(8187))
    

    if not f:
        gpugo.ShowmyGpuInfo()
    if f:
        if k > len(GPUs)-1:
            print(f"There is no gpu device's index  {k}")
            return

        assert os.path.isfile(f), "Please enter correct script path!"
        assign = TaskAssignment(task_path = f,  perdetask = n)
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