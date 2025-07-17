import os
from dotenv import load_dotenv

# Load .env and read the commands folder path
load_dotenv()
COMMANDS_FOLDER = os.getenv("COMMANDS_FOLDER", ".")


def make_circle_commands(radius: int = 100) -> str:
    """
    Approximate a circle by 4 straight-line segments:
    Right -> Top -> Left -> Bottom -> Back to Right
    Returns a multi-line CSV string.
    """
    points = [
        ( radius,   0, 0),
        (   0,  radius, 0),
        (-radius,   0, 0),
        (   0, -radius, 0),
        ( radius,   0, 0),  # close loop
    ]
    cmds = []
    for idx, (x, y, z) in enumerate(points, start=1):
        if idx == 1:
            sx, sy, sz = points[-1]
        else:
            sx, sy, sz = points[idx-2]
        ex, ey, ez = x, y, z
        cmds.append(
            f"VisualInspection,1,"
            f"{sx},{sy},{sz},"
            f"{ex},{ey},{ez},"
            f"-100,150,EOL"
        )
    return "\n".join(cmds)


def _read_command_file(command_name: str) -> str:
    """
    Look for a .csv or .txt file named <command_name> in COMMANDS_FOLDER.
    Returns its full content if found, otherwise raises FileNotFoundError.
    """
    for ext in (".csv", ".txt"):
        path = os.path.join(COMMANDS_FOLDER, command_name + ext)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    raise FileNotFoundError(
        f"No command file '{command_name}.csv' or '{command_name}.txt' found in {COMMANDS_FOLDER}"
    )


def interpret_command(command_name: str, radius: int = 100) -> str:
    """
    Interpret a command by name:
    - If <command_name>.csv or .txt exists in COMMANDS_FOLDER, return its contents.
    - Otherwise, default to generating a circle of given radius.

    :param command_name: Base filename (without extension) to load.
    :param radius: Circle radius in mm for fallback.
    :return: CSV commands as a string.
    """
    try:
        return _read_command_file(command_name)
    except FileNotFoundError:
        # Fallback to default circle path
        return make_circle_commands(radius=radius)
