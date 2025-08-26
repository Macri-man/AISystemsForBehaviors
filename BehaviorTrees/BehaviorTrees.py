# ------------------------------
# Status Enum
# ------------------------------
class Status:
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

# ------------------------------
# Blackboard for shared state
# ------------------------------
class Blackboard:
    def __init__(self):
        self._data = {}

    def set(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

# ------------------------------
# Base Node with logging
# ------------------------------
class Node:
    def __init__(self, name="", blackboard=None):
        self.blackboard = blackboard
        self.name = name

    def tick(self, depth=0):
        raise NotImplementedError("tick() must be implemented by subclasses")

    def log(self, status, depth):
        indent = "  " * depth
        status_str = {Status.SUCCESS: "SUCCESS", Status.FAILURE: "FAILURE", Status.RUNNING: "RUNNING"}[status]
        print(f"{indent}{self.name}: {status_str}")

# ------------------------------
# Composite Nodes
# ------------------------------
class Sequence(Node):
    def __init__(self, children, name="Sequence", blackboard=None):
        super().__init__(name, blackboard)
        self.children = children
        self.current = 0

    def tick(self, depth=0):
        while self.current < len(self.children):
            status = self.children[self.current].tick(depth + 1)
            if status == Status.RUNNING:
                self.log(Status.RUNNING, depth)
                return Status.RUNNING
            elif status == Status.FAILURE:
                self.current = 0
                self.log(Status.FAILURE, depth)
                return Status.FAILURE
            else:
                self.current += 1
        self.current = 0
        self.log(Status.SUCCESS, depth)
        return Status.SUCCESS

class Selector(Node):
    def __init__(self, children, name="Selector", blackboard=None):
        super().__init__(name, blackboard)
        self.children = children
        self.current = 0

    def tick(self, depth=0):
        while self.current < len(self.children):
            status = self.children[self.current].tick(depth + 1)
            if status == Status.RUNNING:
                self.log(Status.RUNNING, depth)
                return Status.RUNNING
            elif status == Status.SUCCESS:
                self.current = 0
                self.log(Status.SUCCESS, depth)
                return Status.SUCCESS
            else:
                self.current += 1
        self.current = 0
        self.log(Status.FAILURE, depth)
        return Status.FAILURE

# ------------------------------
# Decorator Nodes
# ------------------------------
class Inverter(Node):
    def __init__(self, child, name="Inverter", blackboard=None):
        super().__init__(name, blackboard)
        self.child = child

    def tick(self, depth=0):
        status = self.child.tick(depth + 1)
        if status == Status.SUCCESS:
            self.log(Status.FAILURE, depth)
            return Status.FAILURE
        elif status == Status.FAILURE:
            self.log(Status.SUCCESS, depth)
            return Status.SUCCESS
        self.log(status, depth)
        return status

class Repeater(Node):
    def __init__(self, child, times=-1, name="Repeater", blackboard=None):
        super().__init__(name, blackboard)
        self.child = child
        self.times = times
        self.count = 0

    def tick(self, depth=0):
        status = self.child.tick(depth + 1)
        if status == Status.RUNNING:
            self.log(Status.RUNNING, depth)
            return Status.RUNNING
        self.count += 1
        if self.times == -1 or self.count < self.times:
            self.log(Status.RUNNING, depth)
            return Status.RUNNING
        self.count = 0
        self.log(Status.SUCCESS, depth)
        return Status.SUCCESS

class Wait(Node):
    def __init__(self, ticks, name="Wait", blackboard=None):
        super().__init__(name, blackboard)
        self.ticks = ticks
        self.elapsed = 0

    def tick(self, depth=0):
        if self.elapsed < self.ticks:
            self.elapsed += 1
            self.log(Status.RUNNING, depth)
            return Status.RUNNING
        self.elapsed = 0
        self.log(Status.SUCCESS, depth)
        return Status.SUCCESS

class Succeeder(Node):
    def __init__(self, child, name="Succeeder", blackboard=None):
        super().__init__(name, blackboard)
        self.child = child

    def tick(self, depth=0):
        self.child.tick(depth + 1)
        self.log(Status.SUCCESS, depth)
        return Status.SUCCESS

class UntilSuccess(Node):
    def __init__(self, child, name="UntilSuccess", blackboard=None):
        super().__init__(name, blackboard)
        self.child = child

    def tick(self, depth=0):
        status = self.child.tick(depth + 1)
        if status == Status.SUCCESS:
            self.log(Status.SUCCESS, depth)
            return Status.SUCCESS
        self.log(Status.RUNNING, depth)
        return Status.RUNNING

# ------------------------------
# Leaf Nodes
# ------------------------------
class Action(Node):
    def __init__(self, action_func, name="Action", blackboard=None):
        super().__init__(name, blackboard)
        self.action_func = action_func

    def tick(self, depth=0):
        status = self.action_func(self.blackboard)
        self.log(status, depth)
        return status

class Condition(Node):
    def __init__(self, condition_func, name="Condition", blackboard=None):
        super().__init__(name, blackboard)
        self.condition_func = condition_func

    def tick(self, depth=0):
        status = Status.SUCCESS if self.condition_func(self.blackboard) else Status.FAILURE
        self.log(status, depth)
        return status

# ------------------------------
# Example Usage with Logging
# ------------------------------
if __name__ == "__main__":
    bb = Blackboard()
    bb.set("enemy_distance", 5)

    def is_enemy_visible(bb):
        return bb.get("enemy_distance", 100) < 10

    def move_to_enemy(bb):
        dist = bb.get("enemy_distance")
        if dist > 0:
            print(f"  [Action] Moving towards enemy, distance {dist}")
            bb.set("enemy_distance", dist - 2)
            return Status.RUNNING
        print("  [Action] Reached enemy!")
        return Status.SUCCESS

    def attack_enemy(bb):
        print("  [Action] Attacking enemy!")
        return Status.SUCCESS

    # Behavior tree with logging
    tree = Sequence([
        Condition(is_enemy_visible, name="EnemyVisible", blackboard=bb),
        UntilSuccess(Action(move_to_enemy, name="MoveToEnemy", blackboard=bb)),
        Wait(2, name="WaitBeforeAttack", blackboard=bb),
        Succeeder(Action(attack_enemy, name="AttackEnemy", blackboard=bb))
    ], name="RootSequence", blackboard=bb)

    # Tick the tree multiple times
    for i in range(8):
        print(f"\n=== Tick {i+1} ===")
        tree.tick()
