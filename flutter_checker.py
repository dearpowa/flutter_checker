import os
import subprocess
from enum import Enum
from typing import Optional
import sys

import yaml


class System(Enum):
    WINDOWS = "nt"
    MAC = "posix"
    OTHER = "other"

    @staticmethod
    def get_current_system() -> "System":
        if os.name == "nt":
            return System.WINDOWS
        elif os.name == "posix":
            return System.MAC
        else:
            return System.OTHER


project_version: Optional[str] = None
system: System = System.get_current_system()
flutter_version: Optional[str] = None
flutter_path: Optional[str] = None


def __run(command: str, cwd: Optional[str] = None) -> str:
    return subprocess.check_output(command, shell=True, cwd=cwd).decode("utf-8")


# read string from file
def read_file(file_name: str) -> str:
    with open(file_name, "r") as f:
        return f.read()


def get_flutter_version() -> str:
    __run("flutter doctor")
    output = __run("flutter --version")
    return output.split("\n")[0].split(" ")[1]


def get_flutter_path() -> str:
    if system is System.WINDOWS:
        result = __run("where flutter").split("\n")[0].split("\\")
        del result[-1]
        return "\\".join(result)
    else:
        result = __run("which flutter").strip().split("/")
        del result[-1]
        return "/".join(result)


def get_project_version() -> Optional[str]:
    with open("pubspec.yaml", "r") as f:
        pubspec: Optional[dict] = yaml.safe_load(f)
        return (
            pubspec["environment"]["flutter"]
            if pubspec is not None and "environment" in pubspec and "flutter" in pubspec["environment"]
            else None
        )


def print_status() -> None:
    print(
        "Project version: " + (project_version if project_version is not None else "None")
    )
    print("Flutter version: " + flutter_version)
    print("Flutter path: " + flutter_path)


def update_status() -> None:
    global project_version, flutter_version, flutter_path
    project_version = get_project_version()
    flutter_version = get_flutter_version()
    flutter_path = get_flutter_path()


def run() -> None:
    next_dir = None

    try:
        next_dir = sys.argv[1]

        # check if next_dir exists and is a valid path
        if not os.path.exists(next_dir):
            print(f"Path {next_dir} does not exist.")
            return

        # make next_dir absolute if it is not
        if not os.path.isabs(next_dir):
            next_dir = os.path.abspath(next_dir)

        os.chdir(next_dir)
    except Exception:
        print("No directory specified. Using current directory.")
        pass

    if next_dir is not None:
        os.chdir(next_dir)

    current_dir = os.getcwd()

    print(f"Current directory: {current_dir}")
    print("Loading Flutter version...")
    update_status()
    print_status()

    if project_version is None:
        print(
            "Project flutter version is not set.\nPlease set it in pubspec.yaml -> environment -> flutter."
        )
        return

    if project_version != flutter_version:
        print("Flutter version is not synced with project version. Syncing...")
        print(__run(f"git checkout {project_version}", cwd=flutter_path))
        print("Running flutter doctor...")
        __run("flutter doctor")
        __run("flutter clean")
        __run("flutter pub upgrade")
        if system is System.MAC:
            __run("pod update", cwd="./ios")
        print("Completed.")
        update_status()
        print_status()
    else:
        print("Flutter version is synced with project version.")


if __name__ == "__main__":
    run()
