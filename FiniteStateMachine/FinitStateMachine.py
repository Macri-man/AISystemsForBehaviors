class FSM:
    def __init__(self, initial_state, transitions, actions=None):
        self.current_state = initial_state
        self.transitions = transitions
        self.actions = actions or {"on_enter": {}, "on_exit": {}}
        self._trigger_action("on_enter", self.current_state)

    def _trigger_action(self, action_type, state):
        if action_type in self.actions and state in self.actions[action_type]:
            self.actions[action_type][state]()

    def trigger(self, event):
        state_transitions = self.transitions.get(self.current_state, {})
        transition = state_transitions.get(event, None)

        if transition:
            next_state, guard = transition
            if guard is None or guard():
                self._trigger_action("on_exit", self.current_state)
                print(f"Transition: {self.current_state} --({event})--> {next_state}")
                self.current_state = next_state
                self._trigger_action("on_enter", self.current_state)
            else:
                print(f"Guard blocked transition from {self.current_state} on '{event}'")
        else:
            print(f"No transition from {self.current_state} on event '{event}'")


# Example action functions and guard
def can_resume():
    return True

def on_enter_running():
    print(">>> Entered Running: Start moving!")

def on_exit_running():
    print("<<< Exiting Running: Stop moving!")


def main():
    # Define transitions: state -> {event: (next_state, guard_function)}
    transitions = {
        "Idle": {"start": ("Running", None)},
        "Running": {"pause": ("Paused", None), "stop": ("Stopped", None)},
        "Paused": {"resume": ("Running", can_resume), "stop": ("Stopped", None)},
        "Stopped": {}
    }

    # Define actions: on_enter/on_exit callbacks
    actions = {
        "on_enter": {"Running": on_enter_running},
        "on_exit": {"Running": on_exit_running}
    }

    # Create FSM
    fsm = FSM(initial_state="Idle", transitions=transitions, actions=actions)

    # Trigger some events
    fsm.trigger("start")   # Idle -> Running
    fsm.trigger("pause")   # Running -> Paused
    fsm.trigger("resume")  # Paused -> Running
    fsm.trigger("stop")    # Running -> Stopped
    fsm.trigger("start")   # No transition


if __name__ == "__main__":
    main()
