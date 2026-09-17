import os
import re
import subprocess
import sys
from functools import cache

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff")
INCLUDED_DIR = os.path.join("kiwi-shell", "assets", "wallpapers")


def query_wallpaper() -> str | None:
    """The picture awww is showing, under the path awww reports for it."""
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
            return line.split("image: ", 1)[1].strip()

    print("ERROR: awww is not showing an image", file=sys.stderr)
    return None


def get_wallpaper_path() -> str | None:
    return same_included(query_wallpaper())


def set_wallpaper(path: str):
    subprocess.Popen(
        ["awww", "img", path, "--transition-type", "wipe", "--transition-fps", "120"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# kept for the session: the current wallpaper points at the folder only while it is
# an included one, and the grid shouldn't lose them the moment you pick your own
@cache
def included_folder() -> str | None:
    """The wallpapers kiwi-shell ships, found through the XDG data dirs or the current one."""
    data_dirs = [os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")]
    data_dirs += (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
    for data_dir in data_dirs:
        folder = os.path.join(data_dir, INCLUDED_DIR)
        if os.path.isdir(folder):
            return os.path.realpath(folder)
    # installed through home-manager the shell is in no data dir at all, and the
    # only trace of where it keeps them is the wallpaper it set from there
    folder = os.path.dirname(query_wallpaper() or "")
    return folder if folder.endswith(INCLUDED_DIR) else None


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


def library_folder() -> str | None:
    """Your own wallpapers, ~/Pictures/Wallpapers when you keep one."""
    folder = os.path.join(pictures_folder(), "Wallpapers")
    # awww reports resolved paths, so compare resolved paths
    return os.path.realpath(folder) if os.path.isdir(folder) else None


def _images_in(folder: str | None) -> list[str]:
    try:
        names = sorted(os.listdir(folder), key=str.lower) if folder else []
    except OSError:
        names = []
    return [
        os.path.join(folder, name)
        for name in names
        if name.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(os.path.join(folder, name))
    ]


def list_wallpapers(current: str | None = None) -> list[str]:
    """The included wallpapers and your own, the current one first when it's neither."""
    paths = _images_in(included_folder())
    paths += [path for path in _images_in(library_folder()) if same_included(path) not in paths]
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
