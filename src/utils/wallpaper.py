import subprocess
import sys


def get_wallpaper_path() -> str | None:
    result = subprocess.run(
        ["swww", "query"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"ERROR: swww query failed (exit {result.returncode}):\n{result.stderr}", file=sys.stderr)
        return None

    if not result.stdout.strip():
        print("ERROR: swww produced no output", file=sys.stderr)
        return None

    # swww query output looks like:
    # DP-1: image: /path/to/wallpaper.jpg
    # DP-2: image: /path/to/wallpaper.jpg
    first_line = result.stdout.splitlines()[0]

    try:
        path = first_line.split("image: ")[1].strip()
        return path
    except IndexError:
        print(f"ERROR: could not parse swww output: {repr(first_line)}", file=sys.stderr)
        return None


if __name__ == "__main__":
    path = get_wallpaper_path()
    if path:
        print(path)