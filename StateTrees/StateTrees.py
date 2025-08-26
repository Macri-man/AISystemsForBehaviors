import time
from typing import Callable, List, Optional, Dict
import random

# ---------------------------
# Base Classes (Tasks, Decorators, Events)
# ---------------------------

class Task:
    def __init__(self, action: Callable[[], None]):
        self.action = action

    def run(self):
        self.action()

class Decorator:
    def __init__(self, condition: Optional[Callable[[], bool]] = None):
        self.condition = condition or (lambda: True)

    def check(self):
        return self.condition()

class Wait(Decorator):
    def __init__(self, seconds: float):
        super().__init__()
        self.end_time = time.time() + seconds

    def check(self):
        return time.time() >= self.end_time

class Cooldown(Decorator):
    def __init__(self, seconds: float):
        super().__init__()
        self.seconds = seconds
        self.next_time = time.time()

    def check(self):
        if time.time() >= self.next_time:
            self.next_time = time.time() + self.seconds
            return True
        return False

# Event system
class EventSystem:
    def __init__(self):
        self.listeners: Dict[str, List[Callable[[], None]]] = {}

    def register(self, event_name: str, callback: Callable[[], None]):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def trigger(self, event_name: str):
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback()

event_system = EventSystem()

# ---------------------------
# State, Transition, Nodes
# ---------------------------

class Transition:
    def __init__(self, target: 'State', condition: Callable[[], bool], decorators: List[Decorator] = []):
        self.target = target
        self.condition = condition
        self.decorators = decorators

    def is_triggered(self):
        return self.condition() and all(d.check() for d in self.decorators)

class Node:
    def update(self):
        raise NotImplementedError()

class State(Node):
    def __init__(self, name: str):
        self.name = name
        self.tasks: List[Task] = []
        self.transitions: List[Transition] = []
        self.children: List[Node] = []
        self.on_enter: Optional[Callable[[], None]] = None
        self.on_exit: Optional[Callable[[], None]] = None
        self.event_handlers: Dict[str, Callable[[], None]] = {}

    def add_task(self, task: Task):
        self.tasks.append(task)

    def add_transition(self, transition: Transition):
        self.transitions.append(transition)

    def add_child(self, child: Node):
        self.children.append(child)

    def on_event(self, event_name: str, handler: Callable[[], None]):
        self.event_handlers[event_name] = handler
        event_system.register(event_name, handler)

    def enter(self):
        if self.on_enter:
            self.on_enter()
        if self.children:
            self.children[0].enter()

    def exit(self):
        if self.on_exit:
            self.on_exit()

    def update(self):
        for task in self.tasks:
            task.run()
        for t in self.transitions:
            if t.is_triggered():
                self.exit()
                t.target.enter()
                return t.target
        for child in self.children:
            result = child.update()
            if result != child:
                return result
        return self

# Behavior tree nodes
class Sequence(Node):
    def __init__(self, children: List[Node]):
        self.children = children

    def update(self):
        for child in self.children:
            result = child.update()
            if isinstance(result, State) and result != child:
                return result
        return self

class Selector(Node):
    def __init__(self, children: List[Node]):
        self.children = children

    def update(self):
        for child in self.children:
            result = child.update()
            if isinstance(result, State) and result != child:
                return result
        return self

# State Tree
class StateTree:
    def __init__(self, root: Node):
        self.root = root
        if isinstance(root, State):
            self.current_state = root
            self.current_state.enter()
        else:
            self.current_state = None

    def update(self):
        if isinstance(self.root, State):
            self.current_state = self.root.update()
        else:
            self.root.update()

# ---------------------------
# Main AI Simulation
# ---------------------------

def main():
    # Tasks
    idle_task = Task(lambda: print("AI: Idling"))
    patrol_task = Task(lambda: print("AI: Patrolling..."))
    chase_task = Task(lambda: print("AI: Chasing enemy!"))
    attack_task = Task(lambda: print("AI: Attacking!"))

    # States
    idle = State("Idle")
    idle.add_task(idle_task)
    idle.on_enter = lambda: print("Entered Idle")

    patrol = State("Patrol")
    patrol.add_task(patrol_task)
    patrol.on_enter = lambda: print("Entered Patrol")

    chase = State("Chase")
    chase.add_task(chase_task)
    chase.on_enter = lambda: print("Entered Chase")

    attack = State("Attack")
    attack.add_task(attack_task)
    attack.on_enter = lambda: print("Entered Attack")

    # Nested state example
    patrol.add_child(chase)

    # Transitions
    idle.add_transition(Transition(
        target=patrol,
        condition=lambda: True,
        decorators=[Wait(1)]
    ))

    patrol.add_transition(Transition(
        target=chase,
        condition=lambda: random.random() < 0.3,  # 30% chance
        decorators=[Cooldown(2)]
    ))

    chase.add_transition(Transition(
        target=attack,
        condition=lambda: random.random() < 0.5,
        decorators=[Cooldown(1)]
    ))

    attack.add_transition(Transition(
        target=patrol,
        condition=lambda: True,
        decorators=[Wait(2)]
    ))

    # Event triggers
    def enemy_event():
        print("Event: Enemy Detected!")
        chase.enter()

    idle.on_event("EnemyDetected", enemy_event)

    # Complex behavior sequence
    ai_sequence = Sequence([idle, patrol, chase, attack])

    # State Tree
    tree = StateTree(idle)

    # Simulation loop
    for tick in range(10):
        print(f"\n--- Tick {tick} ---")
        tree.update()
        time.sleep(1)
        if tick == 3:
            event_system.trigger("EnemyDetected")

if __name__ == "__main__":
    main()
