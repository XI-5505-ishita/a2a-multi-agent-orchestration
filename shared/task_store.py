# shared/task_store.py

# In-memory task storage
tasks = {}

def create_task(task_id, input_text):
    tasks[task_id] = {
        "status": "pending",
        "input": input_text,
        "result": None
    }


def update_task(task_id, status=None, result=None):

    if task_id not in tasks:
        return

    if status is not None:
        tasks[task_id]["status"] = status

    # always update result
    tasks[task_id]["result"] = result


def get_task(task_id):

    return tasks.get(task_id, {
        "status": "not_found",
        "result": None
    })

    tasks = {}

def create_task(task_id, input_text):
    tasks[task_id] = {
        "status": "pending",
        "input": input_text,
        "result": None
    }
    print("CREATE TASK:", tasks)


def update_task(task_id, status=None, result=None):
    if status is not None:
        tasks[task_id]["status"] = status

    tasks[task_id]["result"] = result

    print("UPDATE TASK:", tasks)


def get_task(task_id):
    print("GET TASK:", tasks)
    return tasks.get(task_id)