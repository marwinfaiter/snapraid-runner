from enum import Enum

class State(Enum):
    SUCCESS = "Run finished successfully"
    FAILED = "Run failed"
    KEYBOARD_INTERRUPT = "Run interrupted by user"
