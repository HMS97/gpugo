import random
import time
import multiprocessing
from subprocess import Popen, PIPE,run
import psutil, os
from  time import sleep
import signal
import shlex
from gpu import GPUgo
# from GPUgo import Pidmem
from collections import OrderedDict
import os
import time

class TaskAssignment:
    # """ this class is for assigning tasks to different GPU devices 

    
    # """
    def __init__(self,task_path = './test_parallel.sh', firstwaitTime = 15, maxdeiveoccmem = 0.9):
        self.task_path = task_path
        self.tasks_string = None
        self.list_pid = []
        self.queue = multiprocessing.Queue()
        self.remian_queue = multiprocessing.Queue()
        self.firstwaitTime = firstwaitTime
        self.maxdeiveoccmem = maxdeiveoccmem
        self.de_assign_task = OrderedDict()
        self.taskmemocc = None
        self.tasktime = multiprocessing.Queue()


    def get_tasks(self):

        file = open(self.task_path,'r', encoding='utf-8')
        tasks = []
        line = file.readlines()
        for item in line:
            tasks.append(item)
        return tasks



   

    def start_procs(self):
        procs = []
        for task_index,task_string in enumerate(self.tasks_string):
            p = multiprocessing.Process(target=self.Run_task, args=(task_string,task_index,self.queue), name=('process_' ))
            procs.append(p)
            p.start()
            print('starting process {}'.format(p.pid))
        return procs

    def Run_task_glance(self,task_string, task_index, queue,device = 0):
        args = shlex.split(task_string)

        os.environ["CUDA_VISIBLE_DEVICES"] = str(device)
        task_info = Popen(args,shell=False, stdout = PIPE,stderr=PIPE,env = os.environ)
        sleep(self.firstwaitTime)
        usedmem = gpugo.Pidmem(task_info.pid)[0]
        sleep(1)
        self.queue.put([task_index, usedmem])
        task_info.kill()

    def Run_task_trian(self,task_index,remian_queue,tasktime,device = 0):

        args = shlex.split(self.tasks_string[task_index])
        os.environ["CUDA_VISIBLE_DEVICES"] = str(device)
        task_info = Popen(args,shell=False, stdout = PIPE,stderr=PIPE,env = os.environ)
        # sleep(16)
        # task_info.kill()
        task_info.wait()
        if  not remian_queue.empty():
            nexttask = remian_queue.get()
           
        while( not remian_queue.empty()):
            
            for device_id in range(len(self.de_assign_task)):
                defreemem = gpugo.MyGpuInfo()[['device_id','memoryFree(MB)']]
                defreemem = defreemem.set_index('device_id',drop=True).T.to_dict('list')
                if(self.maxdeiveoccmem * defreemem[str(device_id)][0] - self.taskmemocc[nexttask] > 0):

                    args = shlex.split(self.tasks_string[task_index])
                    os.environ["CUDA_VISIBLE_DEVICES"] = str(device)

                    lasttime = tasktime.get()
                    nowtime = int(time.time())
                    if (lasttime - nowtime < self.firstwaitTime):
                        sleep(self.firstwaitTime)
                    task_info = Popen(args,shell=False, stdout = PIPE,stderr=PIPE,env = os.environ)
                    tasktime.put( int(time.time() ))
                    # sleep(10)
                    # task_info.kill()
                    task_info.wait()
                    nexttask = remian_queue.get()
                else:
                    sleep(10)   


    # the first time to calcuate every task's used memory for assignment once for each time tasks queue
    def cal_tasks_memory(self):
        self.tasks_string = self.get_tasks()
        tasks_memlist = []
        mem_list = []
        print("calculating the tasks occupied memory!")
        for task_index,task_string in enumerate(self.tasks_string):
            p = multiprocessing.Process(target=self.Run_task_glance, args=(task_string, task_index, self.queue,0), name=('process_' ))
            print(f"calculate task {task_index}")
            p.start()
            p.join()
            tasks_memlist.append(self.queue.get())
        for item in range(len(tasks_memlist)):
            mem_list.append(tasks_memlist[item][1])

        return mem_list

    
    def assign(self, sorted_li,sorted_index):
        print(sorted_index)

        defreemem = gpugo.MyGpuInfo()[['device_id','memoryFree(MB)']]
        defreemem = defreemem.set_index('device_id',drop=True).T.to_dict('list')

        for i in range(len(defreemem)):
            self.de_assign_task[str(i)] = []

        for device in defreemem.keys():
            curr_assignmem = 0
       
        ## two things: the free memory and remaining task in queue 
            while( self.maxdeiveoccmem * defreemem[device][0] - curr_assignmem > 0 and len(sorted_li) > 0 ):
                if (  self.maxdeiveoccmem * defreemem[device][0] - curr_assignmem <  sorted_li[0]):
                    break
                else:
                    task_toadd = sorted_li.pop(0)
                    tindex_toadd = sorted_index.pop(0)
                    curr_assignmem = curr_assignmem + task_toadd
                    self.de_assign_task[device].append(tindex_toadd)
            if len(sorted_index) == 0:
                break

        print('>>>: ', self.de_assign_task, "left task", sorted_li)
        
        return sorted_li,sorted_index

    def start_multi(self):
        procs = []
        temp_time = 0
        self.tasktime.put(int(round(time.time() * 1000)))
        try:
            
            for i in range(len(self.de_assign_task)):
                for task in self.de_assign_task[str(i)][:]:#copy and then delete from list
                    self.de_assign_task[str(i)].pop(0)
                    p = multiprocessing.Process(target=self.Run_task_trian, args=(task,self.remian_queue,self.tasktime,i), name=('process_' ))
                    p.start()
                    procs.append(p)
            for p in procs:
                p.join()
        except KeyboardInterrupt:
            print ("Caught KeyboardInterrupt, terminating workers")
            for p in procs:
                p.terminate()
                p.join()
        # print(self.de_assign_task)
    
    def run(self):
        remaining_tasknum = 0 
        self.taskmemocc = self.cal_tasks_memory()
        # self.taskmemocc = [109000,1000,2000,3000,200000,4000,5500,4000,1000,8000]

        sorted_li = sorted(self.taskmemocc)
        print('finish tasks glancing here are tasks estimated memory by order: \n', sorted_li)

        sorted_index = sorted(range(len(self.taskmemocc)), key=lambda k: self.taskmemocc[k])
        if sorted_li[0] > max(gpugo.MyGpuInfo()['memoryTotal(MB)'].values):
            print("the smallest model required memory is beyond your device capacity")
            return

        sorted_li,sorted_index = self.assign(sorted_li,sorted_index)
        for i in self.de_assign_task.keys():
            remaining_tasknum += len(self.de_assign_task[i])
        for i in sorted_index:
            self.remian_queue.put(i)
        if (remaining_tasknum): self.start_multi()

if __name__ == "__main__":
    gpugo = GPUgo()
    assign = TaskAssignment()
    assign.run()


#   print(GPUs)
