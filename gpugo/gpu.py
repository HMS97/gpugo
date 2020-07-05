from collections import defaultdict
from subprocess import Popen, PIPE
from multiprocessing import Process
from loguru import logger 
import pandas as pd
import signal
import os 


class ProcessInfo:
    """
    class for processes' information
    """
    def __init__(self,uuid,pid,descrition,used_memory):
        self.pid = int(pid)
        self.uuid = uuid
        self.descrition = descrition
        self.used_memory = int(used_memory)

class GPU:
    """
    class for per GPU device's information
    """
    def __init__(self, GPU_type, GPU_index,uuid, utilizationGPU, memoryTotal, memoryUsed, memoryFree, driver):
        self.GPU_type = GPU_type
        self.GPU_index = GPU_index
        self.uuid = uuid
        self.utilizationGPU = utilizationGPU
        self.memoryTotal = float(memoryTotal)
        self.memoryUsed = float(memoryUsed)
        self.memoryFree = float(memoryFree)
        self.driver = driver
        self.task = None
    
    def GPU_info(self):
        return [self.GPU_type,self.GPU_index,self.utilizationGPU,self.memoryTotal,self.memoryUsed,self.memoryFree,self.memoryUsed/self.memoryTotal,len(self.task)]

    ## get task information from device
    def tasks_info(self):
        if len(self.task) == 0:
            return None
        else:
            col = ['device','pid','descrition','used_memory']
            df = pd.DataFrame(columns=col)

            for item in self.task:
                df.loc[len(df)] = [self.GPU_index,item.pid,item.descrition,item.used_memory]
            return df

    ## kill process
    def kill_process(self):
        try:
            pids = self.tasks_info()['pid'].values
            print(pids)
        except:
            print(f"there are no tasks on device {self.GPU_index}!")
            return 
        for item in pids:
            os.kill(item, signal.SIGKILL)
            print("You kill the processes ", item, "successfully!")
  
       
 
class GPUgo():
    """
    class for analysis the device's information

    """
    def __init__(self,):
        self.GPUs = self.GetGpuInfo()

    def MyGpuInfo(self):
        col = ['device_type','device_id','utilizationGPU(%)','memoryTotal(MB)','memoryUsed(MB)','memoryFree(MB)','memoryusedPercent(%)','task_num']
        df = pd.DataFrame(columns=col)
        for gpu in self.GPUs:
            df.loc[len(df)] = gpu.GPU_info()
        return df


    def ShowmyGpuInfo(self):
        print('====='*25)

        df = self.MyGpuInfo()
        print(df.to_string(index=False))
        print('\n')
        print('-----'*25)
        print(self.GpuProcessInfo())
        print('====='*25)


    def GetGpuInfo(self):
        GPUs= []
        GPU_info = Popen(["nvidia-smi","--query-gpu=name,index,uuid,utilization.gpu,memory.total,memory.used,memory.free,driver_version", "--format=csv,noheader,nounits"], stdout=PIPE)
        stdout, stderror = GPU_info.communicate()
        GPU_info = stdout.decode('UTF-8').strip().split('\n')

        GPU_info = [i.split(', ' ) for i in GPU_info]
        for i in range(len(GPU_info)):
            GPUs.append(GPU(*GPU_info[i]))

        process_info = Popen(["nvidia-smi","--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv,noheader,nounits"], stdout=PIPE)
        stdout, stderror = process_info.communicate()
        process_info = stdout.decode('UTF-8').strip().split('\n')
        process_info = [i.split(', ') for i in process_info]
        for gpu in GPUs:
            processes = []
            for item in process_info:
                if gpu.uuid == item[0]:
                    processes.append(ProcessInfo(*item))
            gpu.task = processes
        return GPUs

    def GpuProcessInfo(self):

        col = ['device','pid','descrition','used_memory']
        df = pd.DataFrame(columns=col)
        for gpu in self.GPUs:
            df = pd.concat([df,gpu.tasks_info()])
        if len(df.dropna()) == 0:
            print(f"there is no task on any device !")
            pass
        else:    
            return df
    
    ## get process's memory by pid
    def Pidmem(self,pid):
        self.GPUs = self.GetGpuInfo()
        df = self.GpuProcessInfo()
        memory = df[df['pid'] == pid]['used_memory'].values
        if ( len(memory) > 0 ):
            return memory
        else:
            print(f"there is no pid {pid} on device")
                    
        



