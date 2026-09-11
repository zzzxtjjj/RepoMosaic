"""Sample RepoAtlas target repository."""

from robot import RobotController
from utils import load_config


def main() -> None:
    """Create a controller from the sample configuration."""
    config = load_config()
    controller = RobotController(config["name"])
    controller.move("station-a")


if __name__ == "__main__":
    main()
