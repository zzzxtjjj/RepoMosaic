"""Small robot controller used in RepoAtlas demonstrations."""


class RobotController:
    """Control a named sample robot."""

    def __init__(self, name: str):
        """Initialize the controller with a robot name."""
        self.name = name

    def move(self, position: str) -> str:
        """Move the robot to a target position."""
        return f"{self.name} moving to {position}"

    def stop(self) -> str:
        """Stop the robot."""
        return f"{self.name} stopped"
