import argparse
import logging
import os
import pathlib
import platform
import requests
import subprocess
import shutil
import tempfile


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
            logging.fatal(f"Unsupported platform {platform.system()} {platform.machine()} ({platform.platform()})")
            return

    logging.info(f"Installing Bismuth CLI {args.version} to {args.dir}")
    with tempfile.NamedTemporaryFile() as tempf:
        with requests.get(f"https://github.com/BismuthCloud/cli/releases/download/v{args.version}/bismuthcli.{triple}", allow_redirects=True, stream=True) as resp:
            if not resp.ok:
                logging.fatal("Binary not found (no such version?)")
                return
            shutil.copyfileobj(resp.raw, tempf)

        tempf.flush()
        binpath = args.dir / 'biscli'

        try:
            os.replace(tempf.name, binpath)
            os.chmod(binpath, 0o755)
        except OSError:
            logging.warning(f"Unable to install to {binpath}, requesting 'sudo' to install and chmod...")
            cmd = [
                "sudo",
                "mv",
                tempf.name,
                str(binpath),
            ]
            logging.info(f"Running {cmd}")
            subprocess.run(cmd)
            cmd = [
                "sudo",
                "chmod",
                "775",
                str(binpath),
            ]
            logging.info(f"Running {cmd}")
            subprocess.run(cmd)

    not_in_path = False
    if args.dir not in [pathlib.Path(p) for p in os.environ['PATH'].split(':')]:
        not_in_path = True
        logging.warning(f"{args.dir} is not in your $PATH - you'll need to add it to your shell rc")

    if args.no_quickstart:
        return

    print()

    if os.environ.get('TERM_PROGRAM') != 'vscode' and os.environ.get('TERMINAL_EMULATOR') != 'JetBrains-JediTerm':
        cmd = "python -m bismuth quickstart"
        if not_in_path:
            cmd += " --cli " + str(binpath)

        print("The CLI is best used inside an IDE.")
        print(f"Please open a terminal in your IDE of choice and run `{cmd}` to launch the quickstart.")
        return

    quickstart(argparse.Namespace(cli=binpath))


def quickstart(args):
    print("First, let's log you in to the Bismuth platform.")
    input(" Press [Enter] to run `biscli login`")
    subprocess.run([args.cli, "login"])

    print("Next, let's import a project you'd like to work on.")
    gh_or_local = ""
    while gh_or_local.lower() not in ("github", "local",):
        gh_or_local = input("Would you like to import a project from GitHub, or use a local repo? [github/local] ")

    if gh_or_local == "github":
        input(f" Press [Enter] to run `biscli import --github`")
        subprocess.run([args.cli, "import", "--github"])
    else:
        if pathlib.Path('./.git').is_dir() and input("Would you like to use the currect directory? [Y/n] ").lower() in ('y', ''):
            repo = pathlib.Path('.')
        else:
            while True:
                repo = pathlib.Path(os.path.expanduser(input("Path to repository: ")))
                if not repo.is_dir():
                    print("Not a directory")
                    continue
                if not (repo / '.git').is_dir():
                    print("Not a git repository")
                    continue
                break
        repo = str(repo.absolute())
        input(f" Press [Enter] to run `biscli import {repo}`")
        subprocess.run([args.cli, "import", repo])

    print("Now you can start chatting!")
    print("You can always chat `/help` for more information, or use `/feedback` to send us feedback or report a bug.")
    input(f" Press [Enter] to run `biscli chat --repo {repo}`")
    subprocess.run([args.cli, "chat", "--repo", repo])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s :: %(message)s')

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
