import math
import random
import time

# -----------------------------
# Utility Functions
# -----------------------------
def linear(value, min_val=0, max_val=1):
    return max(0, min(1, (value - min_val) / (max_val - min_val)))

def inverse_linear(value, min_val=0, max_val=1):
    return 1 - linear(value, min_val, max_val)

def sigmoid(value, k=10, x0=0.5):
    return 1 / (1 + math.exp(-k * (value - x0)))

def exponential(value, base=2):
    return min(1, value**base)

def clamp(value):
    return max(0, min(1, value))

# -----------------------------
# Consideration
# -----------------------------
class Consideration:
    def __init__(self, name, func, weight=1.0):
        self.name = name
        self.func = func
        self.weight = weight

    def evaluate(self, agent):
        value = clamp(self.func(agent))
        weighted_value = value * self.weight
        print(f"  [Consideration] {self.name}: {value:.2f} * {self.weight} = {weighted_value:.2f}")
        return weighted_value

# -----------------------------
# Action
# -----------------------------
class Action:
    def __init__(self, name, priority=1, cooldown=0):
        self.name = name
        self.considerations = []
        self.priority = priority
        self.cooldown = cooldown
        self.last_executed = 0

    def add_consideration(self, consideration):
        self.considerations.append(consideration)

    def is_available(self):
        return time.time() - self.last_executed >= self.cooldown

    def evaluate(self, agent):
        if not self.considerations or not self.is_available():
            return 0
        # Combine multiplicatively
        total_utility = 1.0
        for c in self.considerations:
            total_utility *= c.evaluate(agent)
        # Apply small random noise for natural variation
        total_utility *= random.uniform(0.9, 1.1)
        total_utility = clamp(total_utility)
        print(f"[Action] {self.name} utility: {total_utility:.2f}")
        return total_utility

    def execute(self, agent):
        print(f"Executing action: {self.name}")
        self.last_executed = time.time()

# -----------------------------
# Agent
# -----------------------------
class Agent:
    def __init__(self):
        self.energy = 0.5
        self.hunger = 0.5
        self.enemy_nearby = 0.2
        self.health = 0.8

# -----------------------------
# Main Utility AI Loop
# -----------------------------
def main():
    agent = Agent()

    # Define actions
    eat = Action("Eat", cooldown=5)
    eat.add_consideration(Consideration("Hunger", lambda a: linear(a.hunger)))
    eat.add_consideration(Consideration("Energy", lambda a: inverse_linear(a.energy)))

    rest = Action("Rest", cooldown=10)
    rest.add_consideration(Consideration("Energy", lambda a: inverse_linear(a.energy)))
    rest.add_consideration(Consideration("Hunger", lambda a: inverse_linear(a.hunger)))

    fight = Action("Fight", cooldown=3)
    fight.add_consideration(Consideration("EnemyNearby", lambda a: a.enemy_nearby))
    fight.add_consideration(Consideration("Energy", lambda a: a.energy))
    fight.add_consideration(Consideration("Health", lambda a: a.health))

    actions = [eat, rest, fight]

    # Simulate decision-making loop
    for tick in range(1, 6):
        print(f"\n--- Tick {tick} ---")
        best_action = max(actions, key=lambda a: a.evaluate(agent))
        best_action.execute(agent)
        # Randomly modify agent state for next tick
        agent.energy = clamp(agent.energy - random.uniform(0, 0.2))
        agent.hunger = clamp(agent.hunger + random.uniform(0, 0.2))
        agent.enemy_nearby = random.choice([0, 0.5, 1])
        agent.health = clamp(agent.health - random.uniform(0, 0.1))
        time.sleep(1)

if __name__ == "__main__":
    main()
