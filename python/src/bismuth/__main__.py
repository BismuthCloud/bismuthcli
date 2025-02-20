import argparse
import os
import pathlib
import platform
import requests
import subprocess
import shutil
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
WARNING = "⚠️  " if os.environ.get("TERM") == "xterm-256color" else ""


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
    args.dir = pathlib.Path(args.dir).expanduser()
    args.dir.mkdir(parents=True, exist_ok=True)
    binpath = args.dir / "biscli"
    with requests.get(
        f"https://github.com/BismuthCloud/cli/releases/download/v{args.version}/bismuthcli.{triple}",
        allow_redirects=True,
        stream=True,
    ) as resp:
        if not resp.ok:
            cprint(f"{ERROR}Binary not found (no such version?)", "red")
            return
        with open(binpath, "wb") as binf:
            shutil.copyfileobj(resp.raw, binf)
    os.chmod(binpath, 0o755)

    not_in_path = False
    if args.dir not in [pathlib.Path(p) for p in os.environ["PATH"].split(":")]:
        not_in_path = True

    cprint(f"✅ Installed Bismuth CLI to {binpath}", "green")

    if not_in_path:
        rcfile = None
        if "zsh" in os.environ.get("SHELL", ""):
            if pathlib.Path("~/.zshrc").expanduser().exists():
                rcfile = "~/.zshrc"
            elif pathlib.Path("~/.zprofile").expanduser().exists():
                rcfile = "~/.zprofile"
        elif "bash" in os.environ.get("SHELL", ""):
            if pathlib.Path("~/.bashrc").expanduser().exists():
                rcfile = "~/.bashrc"
            elif pathlib.Path("~/.bash_profile").expanduser().exists():
                rcfile = "~/.bash_profile"
        if rcfile:
            with open(pathlib.Path(rcfile).expanduser(), "a") as rc:
                rc.write(f'\nexport PATH="{args.dir}:$PATH"\n')
            os.environ["PATH"] = f"{args.dir}:{os.environ['PATH']}"
            cprint(
                f"✅ Updated $PATH in {rcfile}",
                "green",
            )
            print(
                "👉 You'll need to close and reopen any existing terminals to use `biscli` in them."
            )
        else:
            cprint(
                f"{WARNING}{args.dir} is not in your $PATH - you'll need to add it to your shell rc.",
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

        print(
            "Please open a terminal in your IDE of choice and run",
            colored(cmd, "light_blue"),
            "to launch the quickstart.",
        )
        return

    quickstart(argparse.Namespace(cli=binpath, no_login=False))


def show_cmd(cmd, confirm=True):
    if confirm:
        input(f" Press [Enter] to run {colored(cmd, 'light_blue')}")
    else:
        print(f"Running {colored(cmd, 'light_blue')}")


def quickstart(args):
    if not args.no_login:
        print("First, let's log you in to the Bismuth platform.")
        show_cmd(
            "biscli login", confirm=False
        )  # this already does another "press any key to open"
        subprocess.run([args.cli, "login"])

        print("")

        try:
            creds = int(
                subprocess.check_output(
                    [args.cli, "billing", "credits-remaining"]
                ).strip()
            )
        except (subprocess.CalledProcessError, ValueError):
            creds = 0

        if creds == 0:
            print("You'll need to purchase credits to use Bismuth.")
            show_cmd("biscli billing refill")
            subprocess.run([args.cli, "billing", "refill"])

    use_sample = input(
        "💭 Would you like to first go through a guided tour with a sample project (this will use about 50 credits of your initial 100 credits)? [Y/n]"
    ).lower() in ("y", "")
    if use_sample:
        print("Great! You'll be able to import your own project after this tour.")

        if (
            shutil.which("node") is None
            or shutil.which("npm") is None
            or subprocess.run(["node", "--version"], stdout=subprocess.PIPE)
            .stdout.decode("utf-8")
            .strip()
            < "v18.0.0"
        ):
            print("You'll need Node.js installed to run the sample project.")
            if input("Would you like me to install it for you? [Y/n] ").lower() in (
                "y",
                "",
            ):
                subprocess.run(
                    "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash",
                    shell=True,
                )
                subprocess.run(
                    [os.environ.get("SHELL", "bash"), "-ic", "nvm install node"]
                )
            else:
                print(
                    f"Please install Node.js manually and restart the quickstart with {colored('python -m bismuth quickstart', 'light_blue')}."
                )
                return

        print("Cloning sample project...")
        repo = "quickstart-sample"
        if os.path.exists(repo):
            shutil.rmtree(repo)
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "https://github.com/BismuthCloud/quickstart-sample",
            ]
        )
        print("")

        fullpath = str(pathlib.Path(repo).resolve())

        print(
            "👉 In another terminal, let's run the project to see what we're working with."
        )
        print(
            f"Run {colored(f'cd {fullpath} && npm i && npm run dev', 'light_blue')} and go to the URL."
        )
        input("Press [Enter] to continue.")

        print("This is a simple TODO app that we'll have Bismuth extend for us.")
        print(
            "💡 Fun fact: Bismuth actually created this project from scratch in a single message!"
        )
        print("")

        print("👉 Now, let's import the repository to Bismuth.")
        print(
            "Run",
            colored(f"biscli import '{fullpath}' --upload", "light_blue"),
            "in another terminal.",
        )
        input("Press [Enter] to continue.")
        print("")

        print("👉 Let's start working with Bismuth.")
        print("In another terminal, open the chat interface:")
        cprint(f"biscli chat --repo '{fullpath}'", "light_blue")
        input("Press [Enter] to continue.")

        print("We're first going to ask Bismuth to add a feature. Send this message:")
        cprint(
            "Hey Bismuth, I need you to add the ability to set due dates on tasks. The date set on a task should be shown in a smaller font and must be on a new line below the title. If a task is past its due date, the task title should be shown in red. Also make sure the date selection box is the same height as the title input and has the same padding.",
            "light_magenta",
        )
        print(
            "Bismuth will now plan out how to complete the task, collect relevant information from the repository, and finally begin working."
        )
        print(
            "And Bismuth works all on its own so you can go grab a cup of coffee while this finishes! ☕️"
        )
        print(
            "💡 In the default 'Full' mode, Bismuth will always write code when you message it and won't respond to simple conversational chat."
        )
        input("Press [Enter] once Bismuth is showing you a diff.")
        print("")

        print(
            f"👉 Bismuth is now showing you the diff of the code it wrote. Press {colored('y', 'yellow')} in the chat terminal to accept the changes."
        )
        print(
            "Now, let's check Bismuth's work. Go back to the running app, refresh the page, and test the new date selection feature."
        )
        print("If there is an issue, just ask Bismuth to fix it!")
        input("Press [Enter] to continue.")
        print("")

        print("👉 Now let's have Bismuth fix an intentionally placed bug.")
        print(f"Open {colored('src/App.tsx', 'light_blue')} and delete the")
        print("    saveTasks(updatedTasks);")
        print(f"line in {colored('handleToggleTask', 'light_blue')} (around line 27).")
        input("Press [Enter] to continue.")

        print("Now tell Bismuth:")
        cprint(
            "It looks like task toggle state is not saved between page refreshes. Can you double check the saving logic in App.tsx?",
            "light_magenta",
        )
        input("Press [Enter] once Bismuth is showing you the diff.")
        print("")

        print(
            f"Examine the diff, press {colored('y', 'yellow')} to accept, and check Bismuth's work again."
        )
        print(
            "Go back to the app, refresh, and ensure that marking a task done is persisted between refreshes."
        )
        input("Press [Enter] to continue.")
        print("")

        print("👉 Finally, let's clean up the project")
        print(
            f"Exit the Bismuth chat interface by hitting {colored('Ctrl+C', 'yellow')}, kill the node development server, and run {colored(f'biscli project delete {repo}', 'light_blue')} to delete the project from Bismuth."
        )
        input("Press [Enter] to continue.")
        print("")

        print("🚀 And that's it!")
        print("")
        print("Bismuth can be used on much more than JavaScript frontends.")
        print(
            "Use it to refactor Java webservers, write Python backends, or even create utility programs in C."
        )
        print("Now let's pick one of your projects to work on.")
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
    show_cmd(f"biscli import {repo}", confirm=False)
    subprocess.run([args.cli, "import", repo])

    if not use_sample:
        cprint("🚀 Now you can start chatting!", "green")

    print(
        f"💡 Use the `{colored('/help', 'light_magenta')}` command in chat for more information, or `{colored('/feedback', 'light_magenta')}` to send us feedback or report a bug."
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
    if pathlib.Path("~/bin").expanduser().is_dir():
        default_install_dir = "~/bin"
    else:
        default_install_dir = "~/.local/bin"
    parser_install_cli.add_argument(
        "--dir",
        type=pathlib.Path,
        help="Directory to install the CLI",
        default=default_install_dir,
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
        default="biscli",
    )
    parser_quickstart.add_argument(
        "--no-login",
        help="Skip the login step",
        action="store_true",
    )
    parser_quickstart.set_defaults(func=quickstart)

    args = parser.parse_args()
    args.func(args)
