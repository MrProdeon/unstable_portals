from dataclasses import dataclass


@dataclass
class ActionState:
    allowed: bool = True
    reason: str = ""                 # почему действие запрещено
    needs_confirmation: bool = False
    warning: str = ""                # текст предупреждения для подтверждения


def evaluate(portal, action):
    """Пока все действия разрешены. Правила появятся в пункте 4."""
    return ActionState()