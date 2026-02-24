tasks = {}


def create_task(task_id, input_text):
    tasks[task_id] = {
        "status": "pending",
        "input": input_text,
        "result": None
    }


def update_task(task_id, status=None, result=None):
    if status:
        tasks[task_id]["status"] = status
    if result:
        tasks[task_id]["result"] = result


def get_task(task_id):
    return tasks.get(task_id)