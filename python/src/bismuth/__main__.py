import argparse
import os
import pathlib
import platform
import requests
import subprocess
import shutil
import tempfile
from termcolor import colored, cprint
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

LOGO = r"""
 ____  _                     _   _
| __ )(_)___ _ __ ___  _   _| |_| |__
|  _ \| / __| '_ ` _ \| | | | __| '_ \
| |_) | \__ \ | | | | | |_| | |_| | | |
|____/|_|___/_| |_| |_|\__,_|\__|_| |_|
"""

ERROR = "❌ " if os.environ.get("TERM") == "xterm-256color" else ""
WARNING = "⚠️ " if os.environ.get("TERM") == "xterm-256color" else ""


def install_cli(args):
    if args.version == "LATEST":
        args.version = requests.get(
            "https://bismuthcloud.github.io/cli/LATEST"
        ).text.strip()

    system, machine = platform.system(), platform.machine()
    if system == "Darwin" and machine == "arm64":
        triple = "aarch64-apple-darwin"
    elif system == "Darwin" and machine == "x86_64":
        triple = "x86_64-apple-darwin"
    elif system == "Linux" and machine == "aarch64":
        triple = "aarch64-unknown-linux-gnu"
    elif system == "Linux" and machine == "x86_64":
        triple = "x86_64-unknown-linux-gnu"
    # elif system == "Windows" and machine == "aarch64":
    #     triple = "aarch64-pc-windows-gnu"
    # elif system == "Windows" and machine == "x86_64":
    #     triple = "x86_64-pc-windows-gnu"
    else:
        cprint(
            f"{ERROR}Unsupported platform {platform.system()} {platform.machine()} ({platform.platform()})",
            "red",
        )
        return

    cprint(LOGO, "light_magenta")
    print()
    print(f"Installing Bismuth CLI {args.version} to {args.dir}")
    tempfn = tempfile.mktemp()
    with requests.get(
        f"https://github.com/BismuthCloud/cli/releases/download/v{args.version}/bismuthcli.{triple}",
        allow_redirects=True,
        stream=True,
    ) as resp:
        if not resp.ok:
            cprint(f"{ERROR}Binary not found (no such version?)", "red")
            return
        with open(tempfn, "wb") as tempf:
            shutil.copyfileobj(resp.raw, tempf)

    binpath = args.dir / "biscli"

    try:
        os.replace(tempfn, binpath)
        os.chmod(binpath, 0o755)
    except OSError:
        print(
            f"Unable to install to {binpath}, requesting 'sudo' to install and chmod..."
        )
        cmd = [
            "sudo",
            "mv",
            tempfn,
            str(binpath),
        ]
        print(f"Running {cmd}")
        subprocess.run(cmd)
        cmd = [
            "sudo",
            "chmod",
            "775",
            str(binpath),
        ]
        print(f"Running {cmd}")
        subprocess.run(cmd)

    not_in_path = False
    if args.dir not in [pathlib.Path(p) for p in os.environ["PATH"].split(":")]:
        not_in_path = True
        cprint(
            f"{WARNING}{args.dir} is not in your $PATH - you'll need to add it to your shell rc",
            "yellow",
        )

    if args.no_quickstart:
        return

    print()

    if (
        os.environ.get("TERM_PROGRAM") != "vscode"
        and os.environ.get("TERMINAL_EMULATOR") != "JetBrains-JediTerm"
    ):
        cmd = "python -m bismuth quickstart"
        if not_in_path:
            cmd += " --cli " + str(binpath)

        cprint(
            f"Please open a terminal in your IDE of choice and run {cmd} to launch the quickstart.",
            "light_blue",
            attrs=["bold"],
        )
        return

    quickstart(argparse.Namespace(cli=binpath))


def show_cmd(cmd, confirm=True):
    if confirm:
        input(f" Press [Enter] to run {colored(cmd, 'light_blue')}")
    else:
        print(f"Running {colored(cmd, 'light_blue')}")


def quickstart(args):
    print("First, let's log you in to the Bismuth platform.")
    show_cmd(
        "biscli login", confirm=False
    )  # this already does another "press any key to open"
    subprocess.run([args.cli, "login"])

    print("")
    print("💭 Would you like to use our sample project to start with?")
    if input(
        "If not, you'll be able to pick any repository on your computer. [Y/n] "
    ).lower() in ("y", ""):
        print("Cloning sample project...")
        if os.path.exists("quickstart-sample"):
            shutil.rmtree("quickstart-sample")
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "https://github.com/BismuthCloud/quickstart-sample",
            ]
        )
        print("")

        repo = "quickstart-sample"
        print("👉 First, import the repository to Bismuth")
        show_cmd(f"biscli import {repo}")
        subprocess.run([args.cli, "import", repo])
        print("")

        fullpath = str(pathlib.Path(repo).resolve())

        print(
            "👉 In another terminal, let's run the project to see what we're working with."
        )
        print(
            f"cd to {colored(fullpath, 'light_blue')} and run {colored('npm i && npm run dev', 'light_blue')} and go to the URL."
        )
        input("Press [Enter] to continue.")

        print("This is a simple TODO app that we'll have Bismuth extend for us.")
        print(
            "💡 Fun fact: Bismuth actually created this project from scratch in a single message!"
        )
        input(
            "Once you've explored the app, kill the development server and press [Enter] to continue the guide."
        )
        print("")

        print("👉 Let's start chatting with Bismuth.")
        print("In your second terminal, open the chat interface:")
        cprint(f"biscli chat --repo {fullpath}", "light_blue", attrs=["bold"])
        input("Press [Enter] to continue.")

        print("We're first going to ask Bismuth to add a feature. Send this message:")
        cprint(
            "Hey Bismuth, I need you to add the ability to set due dates on tasks. If a task is past its due date, it should be highlighted.",
            "magenta",
        )
        print(
            "Bismuth will now plan out how to complete the task, collect relevant information from the repository, and finally begin working."
        )
        input("Press [Enter] once Bismuth has finished.")
        print("")

        print(
            f"👉 Bismuth is now showing you the diff of the code it wrote. Press {colored('y', 'yellow')} to accept the changes."
        )
        print(
            f"Now, let's check Bismuth's work. Hit {colored('Esc', 'yellow')} to exit the chat interface, run {colored('npm run dev', 'light_blue')} again, and test the new date selection feature."
        )
        print(
            "If there is an issue, just launch the chat again, describe the issue, and ask Bismuth to fix it!"
        )
        input(
            "Once you're done, kill the development server and press [Enter] to continue."
        )
        print("")

        print("👉 We're now going to have Bismuth fix an intentionally placed bug.")
        print(f"Open {colored('src/App.tsx', 'light_blue')} and delete the")
        print("    saveTasks(updatedTasks);")
        print(f"line in {colored('handleToggleTask', 'light_blue')}.")
        input("Press [Enter] to continue.")

        print("Start the chat again, and send:")
        cprint(
            "It looks like task toggle state is not saved between page refreshes. Can you fix that?",
            "magenta",
        )
        input("Press [Enter] once Bismuth has finished.")
        print("")

        print(
            f"Examine the diff, press {colored('y', 'yellow')} to accept, and let's check Bismuth's work again."
        )
        print(
            f"Run {colored('npm run dev', 'light_blue')} and make sure toggling a task completed is persisted across refreshes."
        )
        input("Press [Enter] to continue.")
        print("")

        print("👉 Finally, let's delete the project")
        print(f"Run {colored(f'biscli project delete {repo}', 'light_blue')}")
        input("Press [Enter] to continue.")
        print("")

        print("🚀 And that's it!")
        print(
            f"You can now import your own project with {colored('biscli import {path}', 'light_blue')} and begin chatting!"
        )
        print(
            f"💡 Use the `{colored('/help', 'light_blue')}` command in chat for more information, or `{colored('/feedback', 'light_blue')}` to send us feedback or report a bug."
        )
    else:
        print("Let's import a project you'd like to work on.")
        if pathlib.Path("./.git").is_dir() and input(
            "Would you like to use the currect directory? [Y/n] "
        ).lower() in ("y", ""):
            repo = pathlib.Path(".")
        else:
            while True:
                repo = pathlib.Path(
                    prompt(
                        "Path to repository: ",
                        completer=PathCompleter(only_directories=True),
                    )
                )
                if not (repo / ".git").is_dir():
                    print("Not a git repository")
                    continue
                break
        repo = str(repo.absolute())
        show_cmd(f"biscli import {repo}")
        subprocess.run([args.cli, "import", repo])

        cprint("🚀 Now you can start chatting!", "green")
        print(
            f"💡 Use the `{colored('/help', 'light_blue')}` command in chat for more information, or `{colored('/feedback', 'light_blue')}` to send us feedback or report a bug."
        )
        if repo == str(pathlib.Path(".").absolute()):
            show_cmd("biscli chat")
        else:
            show_cmd(f"biscli chat --repo {repo}")
        subprocess.run([args.cli, "chat", "--repo", repo])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    parser_install_cli = subparsers.add_parser(
        "install-cli", help="Install the Bismuth Cloud CLI"
    )
    parser_install_cli.add_argument(
        "--dir",
        type=pathlib.Path,
        help="Directory to install the CLI",
        default="/usr/local/bin/",
    )
    parser_install_cli.add_argument(
        "--version", type=str, help="Version to install", default="LATEST"
    )
    parser_install_cli.add_argument(
        "--no-quickstart", help="Skip quickstart", action="store_true"
    )
    parser_install_cli.set_defaults(func=install_cli)

    parser_quickstart = subparsers.add_parser(
        "quickstart", help="See how to use the Bismuth Cloud CLI"
    )
    parser_quickstart.add_argument(
        "--cli",
        type=pathlib.Path,
        help="Path to installed Bismuth CLI",
        default="/usr/local/bin/biscli",
    )
    parser_quickstart.set_defaults(func=quickstart)

    args = parser.parse_args()
    args.func(args)
