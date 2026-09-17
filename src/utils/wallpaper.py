import os
import re
import subprocess
import sys

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff")


def get_wallpaper_path() -> str | None:
    try:
        result = subprocess.run(["awww", "query"], capture_output=True, text=True)
    except OSError as e:
        print(f"ERROR: awww not available: {e}", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(f"ERROR: awww query failed (exit {result.returncode}):\n{result.stderr}", file=sys.stderr)
        return None

    # awww query output looks like:
    # DP-1: 2560x1440, scale: 1, currently displaying: image: /path/to/wallpaper.jpg
    for line in result.stdout.splitlines():
        if "image: " in line:
            return same_included(line.split("image: ", 1)[1].strip())

    print("ERROR: awww is not showing an image", file=sys.stderr)
    return None


def set_wallpaper(path: str):
    subprocess.Popen(
        ["awww", "img", path, "--transition-type", "wipe", "--transition-fps", "120"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def included_folder() -> str | None:
    """The wallpapers kiwi-shell ships, found through the XDG data dirs."""
    data_dirs = [os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")]
    data_dirs += (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
    for data_dir in data_dirs:
        folder = os.path.join(data_dir, "kiwi-shell", "assets", "wallpapers")
        if os.path.isdir(folder):
            return os.path.realpath(folder)
    return None


def same_included(path: str | None) -> str | None:
    """A picture with an included wallpaper's file name is that wallpaper.

    The names carry the Unsplash photo id: a copy in ~/Pictures, or the
    included one from before an update. Listing it once, as the included one.
    """
    folder = included_folder()
    if not path or not folder:
        return path
    included = os.path.join(folder, os.path.basename(path))
    return included if os.path.exists(included) else path


def pictures_folder() -> str:
    from gi.repository import GLib

    return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) or os.path.expanduser("~/Pictures")


def list_wallpapers(current: str | None = None) -> list[str]:
    """The included wallpapers, and the current one first when it's your own."""
    folder = included_folder()
    try:
        names = sorted(os.listdir(folder), key=str.lower) if folder else []
    except OSError:
        names = []
    paths = [
        os.path.join(folder, name)
        for name in names
        if name.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(os.path.join(folder, name))
    ]
    if current and current not in paths:
        paths.insert(0, current)
    return paths


# "vadim-sadovski-J3e3_mK4MBQ-unsplash.jpg" -> "Vadim Sadovski"
def wallpaper_name(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    unsplash = re.fullmatch(r"(.+)-[A-Za-z0-9_-]{11}-unsplash", base)
    if not unsplash:
        return base
    return " ".join(word.capitalize() for word in unsplash.group(1).split("-"))


if __name__ == "__main__":
    path = get_wallpaper_path()
    if path:
        print(path)
