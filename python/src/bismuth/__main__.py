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
    if args.version == 'LATEST':
        args.version = requests.get('https://bismuthcloud.github.io/cli/LATEST').text.strip()
    match (platform.system(), platform.machine()):
        case ("Darwin", "arm64"):
            triple = "aarch64-apple-darwin"
        case ("Darwin", "x86_64"):
            triple = "x86_64-apple-darwin"
        case ("Linux", "aarch64"):
            triple = "aarch64-unknown-linux-gnu"
        case ("Linux", "x86_64"):
            triple = "x86_64-unknown-linux-gnu"
        # case ("Windows", "aarch64"):
        #     triple = "aarch64-pc-windows-gnu"
        # case ("Windows", "x86_64"):
        #     triple = "x86_64-pc-windows-gnu"
        case _:
            cprint(f"{ERROR}Unsupported platform {platform.system()} {platform.machine()} ({platform.platform()})", "red")
            return

    cprint(LOGO, 'light_magenta')
    print()
    print(f"Installing Bismuth CLI {args.version} to {args.dir}")
    tempfn = tempfile.mktemp()
    with requests.get(f"https://github.com/BismuthCloud/cli/releases/download/v{args.version}/bismuthcli.{triple}", allow_redirects=True, stream=True) as resp:
        if not resp.ok:
            cprint(f"{ERROR}Binary not found (no such version?)", "red")
            return
        with open(tempfn, 'wb') as tempf:
            shutil.copyfileobj(resp.raw, tempf)

    binpath = args.dir / 'biscli'

    try:
        os.replace(tempfn, binpath)
        os.chmod(binpath, 0o755)
    except OSError:
        print(f"Unable to install to {binpath}, requesting 'sudo' to install and chmod...")
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
    if args.dir not in [pathlib.Path(p) for p in os.environ['PATH'].split(':')]:
        not_in_path = True
        cprint(f"{WARNING}{args.dir} is not in your $PATH - you'll need to add it to your shell rc", "yellow")

    if args.no_quickstart:
        return

    print()

    if os.environ.get('TERM_PROGRAM') != 'vscode' and os.environ.get('TERMINAL_EMULATOR') != 'JetBrains-JediTerm':
        cmd = "python -m bismuth quickstart"
        if not_in_path:
            cmd += " --cli " + str(binpath)

        print(f"Please open a terminal in your IDE of choice and run `{colored(cmd, 'light_blue')}` to launch the quickstart.")
        return

    quickstart(argparse.Namespace(cli=binpath))


def show_cmd(cmd):
    input(f" Press [Enter] to run `{colored(cmd, 'light_blue')}`")

def quickstart(args):
    print("First, let's log you in to the Bismuth platform.")
    show_cmd("biscli login")
    subprocess.run([args.cli, "login"])

    print("Next, let's import a project you'd like to work on.")
    if pathlib.Path('./.git').is_dir() and input("Would you like to use the currect directory? [Y/n] ").lower() in ('y', ''):
        repo = pathlib.Path('.')
    else:
        while True:
            repo = pathlib.Path(prompt("Path to repository: ", completer=PathCompleter(only_directories=True)))
            if not (repo / '.git').is_dir():
                print("Not a git repository")
                continue
            break
    repo = str(repo.absolute())
    show_cmd(f"biscli import {repo}")
    subprocess.run([args.cli, "import", repo])

    cprint("🚀 Now you can start chatting!", "green")
    print(f"You can always chat `{colored('/help', 'light_blue')}` for more information, or use `{colored('/feedback', 'light_blue')}` to send us feedback or report a bug.")
    if repo == str(pathlib.Path('.').absolute()):
        show_cmd("biscli chat")
    else:
        show_cmd(f"biscli chat --repo {repo}")
    subprocess.run([args.cli, "chat", "--repo", repo])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    parser_install_cli = subparsers.add_parser('install-cli', help='Install the Bismuth Cloud CLI')
    parser_install_cli.add_argument('--dir', type=pathlib.Path, help='Directory to install the CLI', default='/usr/local/bin/')
    parser_install_cli.add_argument('--version', type=str, help='Version to install', default='LATEST')
    parser_install_cli.add_argument('--no-quickstart', help='Skip quickstart', action='store_true')
    parser_install_cli.set_defaults(func=install_cli)

    parser_quickstart = subparsers.add_parser('quickstart', help='See how to use the Bismuth Cloud CLI')
    parser_quickstart.add_argument('--cli', type=pathlib.Path, help='Path to installed Bismuth CLI', default='/usr/local/bin/biscli')
    parser_quickstart.set_defaults(func=quickstart)

    args = parser.parse_args()
    args.func(args)
