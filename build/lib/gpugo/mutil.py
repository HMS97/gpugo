import random
import time
import multiprocessing
from subprocess import Popen, PIPE,run
from  time import sleep
import signal
import shlex
from .gpu import GPUgo
from collections import OrderedDict
import os
import time
from loguru import logger 

class TaskAssignment:
    r""" this class is for assigning tasks to different GPU devices 

    args:
        task_path: the file's path for your script
        firstwaitTime: the estimation time for the first execution
        maxdeiveoccmem: safe level free memory to ensure no overflow
        perdetask: the maxinum task on each device 
    """
    def __init__(self, task_path, firstwaitTime = 15, maxdeiveoccmem = 0.9 , perdetask = 99):
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
        self.perdetask = perdetask
        self.gpugo = GPUgo()

    ##get task from script
    def get_tasks(self):
        file = open(self.task_path,'r', encoding='utf-8')
        tasks = []
        line = file.readlines()
        for item in line:
            tasks.append(item)
        return tasks


    ##estimate task's occopied memory
    def Run_task_glance(self,task_string, task_index, queue,device = 0):

        args = shlex.split(task_string)
        os.environ["CUDA_VISIBLE_DEVICES"] = str(device)
        task_info = Popen(args,shell=False, stdout = PIPE,stderr=PIPE,env = os.environ)
        sleep(self.firstwaitTime)
        usedmem = self.gpugo.Pidmem(task_info.pid)[0]
        self.queue.put([task_index, usedmem])
        task_info.kill()


    ## execute tasks on mutil process
    def Run_task_trian(self,task_index,remian_queue,tasktime,device = 0):

        args = shlex.split(self.tasks_string[task_index])
        os.environ["CUDA_VISIBLE_DEVICES"] = str(device)
        FNULL = open(os.devnull, 'w')
        task_info = Popen(args,shell=False, stdout = FNULL,stderr=PIPE,env = os.environ)

        task_info.communicate()
        # sleep(15)
        # task_info.kill()
        logger.info(f'{self.tasks_string[task_index]} successful finished! ')

        if (not remian_queue.empty()):
            task_index = remian_queue.get()


        while( not remian_queue.empty()):
           

            for device_id in range(len(self.de_assign_task)):
                defreemem = self.gpugo.MyGpuInfo()[['device_id','memoryFree(MB)']]
                defreemem = defreemem.set_index('device_id',drop=True).T.to_dict('list')

               

                if(self.maxdeiveoccmem * defreemem[str(device_id)][0] - self.taskmemocc[task_index] > 0):

                    args = shlex.split(self.tasks_string[task_index])
                    os.environ["CUDA_VISIBLE_DEVICES"] = str(device)

                    lasttime = tasktime.get()
                    nowtime = int(time.time())
                    if (lasttime - nowtime < self.firstwaitTime):
                        sleep(self.firstwaitTime)
                    task_info = Popen(args,shell=False, stdout = FNULL,stderr=PIPE,env = os.environ)
                    tasktime.put( int(time.time() ))
                    task_info.communicate()

                    # sleep(15)
                    # task_info.kill()
                    logger.info(f'{self.tasks_string[task_index]} successful finished! ')

                    if (not remian_queue.empty()):
                        task_index = remian_queue.get()


                else:
                    sleep(10)   

        task_info.terminate()


    # the first time to calcuate every task's used memory for assignment once for each time tasks queue
    def cal_tasks_memory(self):
        self.tasks_string = self.get_tasks()
        tasks_memlist = []
        mem_list = []
        logger.info("calculating the tasks occupied memory!")
        for task_index,task_string in enumerate(self.tasks_string):
            p = multiprocessing.Process(target=self.Run_task_glance, args=(task_string, task_index, self.queue,0), name=('process_' ))
            p.start()
            p.join()
            temp_memory = self.queue.get()
            tasks_memlist.append(temp_memory)
            logger.info(f"task {task_index}'s  occupied memory is {temp_memory[1]}")

        for item in range(len(tasks_memlist)):
            mem_list.append(tasks_memlist[item][1])

        return mem_list



    ##first assign the task
    def assign(self, sorted_li,sorted_index):
        logger.info(sorted_index)

        defreemem = self.gpugo.MyGpuInfo()[['device_id','memoryFree(MB)']]
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
                    if(len(self.de_assign_task[device]) <  self.perdetask ):
                        task_toadd = sorted_li.pop(0)
                        tindex_toadd = sorted_index.pop(0)
                        curr_assignmem = curr_assignmem + task_toadd
                        self.de_assign_task[device].append(tindex_toadd)
                    else:
                        break

            if len(sorted_index) == 0:
                break

        logger.info(f'first assign {self.de_assign_task}   remaining task  {sorted_li}')
        
        return sorted_li,sorted_index



    ## start the process to run tasks
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
            for p in procs:
                p.terminate()
        except KeyboardInterrupt:
            logger.info ("Caught KeyboardInterrupt, terminating workers")
            for p in procs:
                p.terminate()
                p.join()




    ## pipeline
    def run(self):
        logger.add("./file.log", format="{time} {message}", filter="", level="INFO", enqueue=True) 

        remaining_tasknum = 0 
        self.taskmemocc = self.cal_tasks_memory()
        # self.taskmemocc = [2743,8439,5331,2753,5331,2343,2444]
        sorted_li = sorted(self.taskmemocc)
        logger.info('finish tasks glancing here are tasks estimated memory by order: \t', sorted_li)
        print(self.taskmemocc[1])
        # logger.info('finish tasks glancing here are tasks estimated memory by order: \t', self.taskmemocc[1])

        sorted_index = sorted(range(len(self.taskmemocc)), key=lambda k: self.taskmemocc[k])
        if sorted_li[0] > max(self.gpugo.MyGpuInfo()['memoryTotal(MB)'].values):
            logger.info("the smallest model required memory is beyond your device capacity")
            return
 
        sorted_li,sorted_index = self.assign(sorted_li,sorted_index)
        logger.info(f'sorted_index: {sorted_index}' )
        for i in self.de_assign_task.keys():
            remaining_tasknum += len(self.de_assign_task[i])
        for i in sorted_index:
            self.remian_queue.put(i)
        if (remaining_tasknum): self.start_multi()

