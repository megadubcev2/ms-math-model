import time
from collections import deque

class ProductionTask:
    def __init__(self, task_id, machine_id, start_time, duration, setup_time, pinned=False):
        self.task_id = task_id
        self.machine_id = machine_id
        self.start_time = start_time
        self.duration = duration
        self.setup_time = setup_time
        self.pinned = pinned
        self.end_time = self.start_time + self.duration
        self.predecessors = []  # List of tasks that must precede this task
        self.successors = []    # List of tasks that follow this task

    def __repr__(self):
        return f"Task({self.task_id}, Machine {self.machine_id}, Start {self.start_time}, End {self.end_time})"

class Dependency:
    def __init__(self, predecessor, successor, dep_type, min_lag=0, max_lag=float('inf')):
        self.predecessor = predecessor
        self.successor = successor
        self.dep_type = dep_type  # 'FS', 'SS', 'FF', 'SF'
        self.min_lag = min_lag
        self.max_lag = max_lag

# Main rescheduling function
def reschedule(moved_task, tasks, dependencies, time_limit):
    start_time = time.time()
    adjusted_tasks = set()
    queue = deque()
    queue.append(moved_task)

    while queue:
        # Check time limit
        if time.time() - start_time > time_limit:
            return {"status": "error", "message": "Time limit exceeded", "tasks_adjusted": len(adjusted_tasks)}

        current_task = queue.popleft()

        # Skip if already adjusted
        if current_task.task_id in adjusted_tasks:
            continue
        adjusted_tasks.add(current_task.task_id)

        # Step 3: Conflict Resolution on Machine
        conflicts = find_overlapping_tasks(current_task, tasks)
        for conflict_task in conflicts:
            if conflict_task.pinned:
                if current_task.pinned:
                    return {"status": "error", "message": "Conflict with pinned tasks", "tasks_adjusted": len(adjusted_tasks)}
                else:
                    # Adjust current_task to resolve conflict
                    adjust_task(current_task, conflict_task)
                    queue.append(current_task)
                    break
            else:
                # Adjust conflicting task
                adjust_task(conflict_task, current_task)
                queue.append(conflict_task)

        # Step 4: Dependency Constraint Enforcement
        task_dependencies = get_task_dependencies(current_task, dependencies)
        for dep in task_dependencies:
            if not is_dependency_satisfied(dep):
                linked_task = dep.successor if dep.predecessor == current_task else dep.predecessor
                if linked_task.pinned:
                    if current_task.pinned:
                        return {"status": "error", "message": "Dependency conflict with pinned tasks", "tasks_adjusted": len(adjusted_tasks)}
                    else:
                        # Adjust current_task
                        adjust_task_for_dependency(current_task, linked_task, dep)
                        queue.append(current_task)
                        break
                else:
                    # Adjust linked_task
                    adjust_task_for_dependency(linked_task, current_task, dep)
                    queue.append(linked_task)

        # Step 5: Setup Time Consideration
        adjust_for_setup_times(current_task, tasks)

    return {"status": "success", "tasks_adjusted": len(adjusted_tasks), "adjusted_tasks": adjusted_tasks}

# Helper functions
def find_overlapping_tasks(task, tasks):
    overlapping_tasks = []
    for t in tasks:
        if t.machine_id == task.machine_id and t.task_id != task.task_id:
            if tasks_overlap(task, t):
                overlapping_tasks.append(t)
    return overlapping_tasks

def tasks_overlap(task1, task2):
    start1 = task1.start_time
    end1 = task1.end_time + task1.setup_time
    start2 = task2.start_time
    end2 = task2.end_time + task2.setup_time
    return max(start1, start2) < min(end1, end2)

def adjust_task(task_to_adjust, reference_task):
    # Move task_to_adjust to start after reference_task
    task_to_adjust.start_time = reference_task.end_time + reference_task.setup_time
    task_to_adjust.end_time = task_to_adjust.start_time + task_to_adjust.duration

def get_task_dependencies(task, dependencies):
    task_deps = []
    for dep in dependencies:
        if dep.predecessor == task or dep.successor == task:
            task_deps.append(dep)
    return task_deps

def is_dependency_satisfied(dep):
    pred = dep.predecessor
    succ = dep.successor
    lag = succ.start_time - pred.end_time

    if dep.dep_type == 'FS':
        lag = succ.start_time - pred.end_time
    elif dep.dep_type == 'SS':
        lag = succ.start_time - pred.start_time
    elif dep.dep_type == 'FF':
        lag = succ.end_time - pred.end_time
    elif dep.dep_type == 'SF':
        lag = succ.end_time - pred.start_time
    else:
        return False  # Invalid dependency type

    return dep.min_lag <= lag <= dep.max_lag

def adjust_task_for_dependency(task_to_adjust, reference_task, dep):
    if dep.dep_type == 'FS':
        task_to_adjust.start_time = reference_task.end_time + dep.min_lag
    elif dep.dep_type == 'SS':
        task_to_adjust.start_time = reference_task.start_time + dep.min_lag
    elif dep.dep_type == 'FF':
        task_to_adjust.end_time = reference_task.end_time + dep.min_lag
        task_to_adjust.start_time = task_to_adjust.end_time - task_to_adjust.duration
    elif dep.dep_type == 'SF':
        task_to_adjust.end_time = reference_task.start_time + dep.min_lag
        task_to_adjust.start_time = task_to_adjust.end_time - task_to_adjust.duration

    # Update end_time
    task_to_adjust.end_time = task_to_adjust.start_time + task_to_adjust.duration

def adjust_for_setup_times(task, tasks):
    # Find previous task on the same machine
    previous_tasks = [t for t in tasks if t.machine_id == task.machine_id and t.end_time <= task.start_time and t.task_id != task.task_id]
    if previous_tasks:
        latest_task = max(previous_tasks, key=lambda t: t.end_time)
        # Ensure there's enough time for setup
        if task.start_time < latest_task.end_time + task.setup_time:
            task.start_time = latest_task.end_time + task.setup_time
            task.end_time = task.start_time + task.duration

# Example usage
if __name__ == "__main__":
    # Define tasks
    task_A = ProductionTask('A', 1, 0, 5, 1, pinned=False)
    task_B = ProductionTask('B', 1, 6, 4, 1, pinned=False)
    task_C = ProductionTask('C', 2, 5, 3, 1, pinned=False)
    tasks = [task_A, task_B, task_C]

    # Define dependencies
    dep_AB = Dependency(task_A, task_B, 'FS', min_lag=1)
    dep_BC = Dependency(task_B, task_C, 'FS', min_lag=2)
    dependencies = [dep_AB, dep_BC]

    # User moves task_A to start at time 2
    task_A.start_time = 2
    task_A.end_time = task_A.start_time + task_A.duration

    # Reschedule
    result = reschedule(task_A, tasks, dependencies, time_limit=5)
    if result["status"] == "success":
        print("Rescheduling successful.")
        for t in tasks:
            print(t)
    else:
        print("Rescheduling failed:", result["message"])