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
        case ("Linux", "arm64"):
            triple = "aarch64-unknown-linux-gnu"
        case ("Linux", "x86_64"):
            triple = "x86_64-unknown-linux-gnu"
        case _:
            logging.fatal(f"Unsupported platform {platform.platform()}")
            return

    logging.info(f"Installing bismuthcli {args.version} to {args.dir}")
    with tempfile.NamedTemporaryFile() as tempf:
        with requests.get(f"https://github.com/BismuthCloud/cli/releases/download/v{args.version}/bismuthcli.{triple}", allow_redirects=True, stream=True) as resp:
            if not resp.ok:
                logging.fatal("Binary not found (no such version?)")
                return
            shutil.copyfileobj(resp.raw, tempf)

        tempf.flush()
        binpath = args.dir / 'bismuth'

        try:
            os.replace(tempf.name, binpath)
            os.chmod(binpath, 0o755)
        except OSError:
            logging.warning(f"Unable to install to {binpath}, requesting 'sudo' to install and chmod...")
            subprocess.run([
                "sudo",
                "mv",
                tempf.name,
                str(binpath),
            ])
            subprocess.run([
                "sudo",
                "chmod",
                "775",
                str(binpath),
            ])

    if args.dir not in [pathlib.Path(p) for p in os.environ['PATH'].split(':')]:
        logging.warning(f"{args.dir} is not in your $PATH - you'll need to add it")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    parser_install_cli = subparsers.add_parser('install-cli', help='Install the Bismuth Cloud CLI')
    parser_install_cli.add_argument('--dir', type=pathlib.Path, help='Directory to install the CLI', default='/usr/local/bin/')
    parser_install_cli.add_argument('--version', type=str, help='Version to install', default='LATEST')
    parser_install_cli.set_defaults(func=install_cli)

    args = parser.parse_args()
    args.func(args)
