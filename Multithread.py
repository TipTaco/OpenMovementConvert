# Author Adrian Shedley
# date 28 May 2020
# purpose, contain and track the progress of each of the threads and tasks running

class Task():
    def __init__(self, name:str, taskID:int, type:str):
        self.name = name
        self.taskID = taskID
        self.type = type  # CONVERT, RESAMPLE, WRITE
        self.progress:float = 0.0
        self.done = False

    def update_progress(self, progress:float):
        self.progress = progress

        if (round(progress,1) == 100.0):
            self.done = True

    def is_done(self):
        return self.done

    def get_progress(self):
        return self.progress


TASKS: Task = []

def add_task(task:Task):
    TASKS.append(task)

def all_done():
    for task in TASKS:
        if not task.is_done():
            return False

    return True

def find_ID(ID:int):
    for task in TASKS:
        if task.taskID == ID:
            return task
    return None

def update_ID(ID:int, prog):
    task = find_ID(ID)
    if task is not None:
        #print('progress', task.progress)
        task.update_progress(prog)
    else:
        pass #print("didnt find")

