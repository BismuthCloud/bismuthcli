#!/usr/bin/env node
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import chalk from 'chalk';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as child_process from 'child_process';
import inquirer from 'inquirer';

const LOGO = `
 ____  _                     _   _
| __ )(_)___ _ __ ___  _   _| |_| |__
|  _ \\| / __| '_ \` _ \\| | | | __| '_ \\
| |_) | \\__ \\ | | | | | |_| | |_| | | |
|____/|_|___/_| |_| |_|\\__,_|\\__|_| |_|
`;

function getPlatformTriple(): string {
  const platform = os.platform();
  const arch = os.arch();

  const platformMap: Record<string, Record<string, string>> = {
    darwin: {
      arm64: 'aarch64-apple-darwin',
      x64: 'x86_64-apple-darwin'
    },
    linux: {
      arm64: 'aarch64-unknown-linux-gnu',
      x64: 'x86_64-unknown-linux-gnu'
    }
  };

  if (platformMap[platform] && platformMap[platform][arch]) {
    return platformMap[platform][arch];
  }

  throw new Error(`Unsupported platform: ${platform} ${arch}`);
}

function checkPermissions(installDir: string): boolean {
  try {
    // Check if we have write permissions to the installation directory
    fs.accessSync(installDir, fs.constants.W_OK);
    return true;
  } catch {
    return false;
  }
}

function elevatePermissions(command: string): boolean {
  try {
    // Try sudo on Unix-like systems
    if (process.platform !== 'win32') {
      child_process.execSync(`sudo ${command}`, { stdio: 'inherit' });
      return true;
    }
    return false;
  } catch (error) {
    console.error(chalk.red('❌ Permission elevation failed:'), error);
    return false;
  }
}

async function installCli(argv: any) {
  console.log(chalk.magenta(LOGO));
  console.log();

  const version = argv.cliVersion === 'LATEST' 
    ? await axios.get('https://bismuthcloud.github.io/cli/LATEST').then(r => r.data.trim())
    : argv.cliVersion;

  const installDir = argv.dir || '/usr/local/bin/';
  const binPath = path.join(installDir, 'biscli');

  console.log(`Installing Bismuth CLI ${version} to ${installDir}`);

  try {
    const triple = getPlatformTriple();
    const downloadUrl = `https://github.com/BismuthCloud/cli/releases/download/v${version}/bismuthcli.${triple}`;

    const response = await axios({
      method: 'get',
      url: downloadUrl,
      responseType: 'arraybuffer'
    });

    // Check and handle permissions
    if (!checkPermissions(installDir)) {
      console.log(chalk.yellow(`⚠️  No write access to ${installDir}. Requesting sudo...`));
      
      // Try to create directory with sudo
      const mkdirCommand = `mkdir -p ${installDir}`;
      if (!elevatePermissions(mkdirCommand)) {
        throw new Error(`Cannot create directory ${installDir}. Please check your permissions.`);
      }

      // Try to write file with sudo
      const tempFilePath = path.join(os.tmpdir(), 'bismuthcli');
      fs.writeFileSync(tempFilePath, response.data, { mode: 0o755 });
      
      const sudoMoveCommand = `mv ${tempFilePath} ${binPath}`;
      if (!elevatePermissions(sudoMoveCommand)) {
        throw new Error(`Cannot move file to ${binPath}. Please check your permissions.`);
      }
    } else {
      // If we have permissions, proceed normally
      fs.mkdirSync(installDir, { recursive: true });
      fs.writeFileSync(binPath, response.data, { mode: 0o755 });
    }

    console.log(chalk.green(`✅ Installed Bismuth CLI to ${binPath}`));

    if (!argv.noQuickstart) {
      await quickstart(binPath);
    }
  } catch (error: any) {
    console.error(chalk.red('❌ Installation failed:'), error.message);
    
    // Provide more detailed error guidance
    if (error.message.includes('permissions')) {
      console.log(chalk.yellow('💡 Tip: Try running the installation with sudo or as an administrator.'));
    }
  }
}

async function quickstart(cliPath?: string) {
  console.log("First, let's log you in to the Bismuth platform.");
  
  const loginCmd = cliPath ? `${cliPath} login` : 'biscli login';
  console.log(chalk.blue(`Running: ${loginCmd}`));
  
  child_process.execSync(loginCmd, { stdio: 'inherit' });

  console.log("Next, let's import a project you'd like to work on.");
  
  const isGitRepo = fs.existsSync(path.join(process.cwd(), '.git'));
  let repoPath: string;

  if (isGitRepo) {
    const { useCurrentDir } = await inquirer.prompt([{
      type: 'confirm',
      name: 'useCurrentDir',
      message: 'Would you like to use the current directory?',
      default: true
    }]);

    repoPath = useCurrentDir ? process.cwd() : await selectRepository();
  } else {
    repoPath = await selectRepository();
  }

  const importCmd = cliPath ? `${cliPath} import "${repoPath}"` : `biscli import "${repoPath}"`;
  console.log(chalk.blue(`Press Enter to run: ${importCmd}`));
  await inquirer.prompt([{ type: 'input', name: 'continue', message: 'Press Enter to continue...' }]);
  
  child_process.execSync(importCmd, { stdio: 'inherit' });

  console.log(chalk.green('🚀 Now you can start chatting!'));
  console.log(chalk.blue('You can always chat `/help` for more information, or use `/feedback` to send us feedback or report a bug.'));

  const chatCmd = cliPath ? `${cliPath} chat --repo "${repoPath}"` : `biscli chat --repo "${repoPath}"`;
  console.log(chalk.blue(`Press Enter to run: ${chatCmd}`));
  await inquirer.prompt([{ type: 'input', name: 'continue', message: 'Press Enter to continue...' }]);
  
  child_process.execSync(chatCmd, { stdio: 'inherit' });
}

async function selectRepository(): Promise<string> {
  while (true) {
    const { repoPath } = await inquirer.prompt([{
      type: 'input',
      name: 'repoPath',
      message: 'Path to repository:',
      validate: (input) => {
        const fullPath = path.resolve(input);
        return fs.existsSync(path.join(fullPath, '.git')) 
          ? true 
          : 'Not a git repository';
      }
    }]);

    return path.resolve(repoPath);
  }
}

const parsed = yargs(hideBin(process.argv))
  .command('install', 'Install the Bismuth CLI', (yargs) => {
    return yargs
      .option('dir', {
        type: 'string',
        description: 'Directory to install the CLI',
        default: '/usr/local/bin/'
      })
      .option('cli-version', {
        type: 'string',
        description: 'Version to install',
        default: 'LATEST'
      })
      .option('no-quickstart', {
        type: 'boolean',
        description: 'Skip quickstart',
        default: false
      });
  }, installCli)
  .command('quickstart', 'See how to use the Bismuth CLI', {}, () => quickstart())
  .strict()
  .demandCommand()
  .help()
  .parse();
