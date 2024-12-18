#!/usr/bin/env node
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import chalk from "chalk";
import axios from "axios";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as child_process from "child_process";
import inquirer from "inquirer";

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
      arm64: "aarch64-apple-darwin",
      x64: "x86_64-apple-darwin",
    },
    linux: {
      arm64: "aarch64-unknown-linux-gnu",
      x64: "x86_64-unknown-linux-gnu",
    },
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
    if (process.platform !== "win32") {
      child_process.execSync(`sudo ${command}`, { stdio: "inherit" });
      return true;
    }
    return false;
  } catch (error) {
    console.error(chalk.red("❌ Permission elevation failed:"), error);
    return false;
  }
}

async function installCli(argv: any) {
  console.log(chalk.magenta(LOGO));
  console.log();

  const version =
    argv.cliVersion === "LATEST"
      ? await axios
          .get("https://bismuthcloud.github.io/cli/LATEST")
          .then((r) => r.data.trim())
      : argv.cliVersion;

  const installDir = argv.dir || "/usr/local/bin/";
  const binPath = path.join(installDir, "biscli");

  console.log(`Installing Bismuth CLI ${version} to ${installDir}`);

  try {
    const triple = getPlatformTriple();
    const downloadUrl = `https://github.com/BismuthCloud/cli/releases/download/v${version}/bismuthcli.${triple}`;

    const response = await axios({
      method: "get",
      url: downloadUrl,
      responseType: "arraybuffer",
    });

    // Check and handle permissions
    if (!checkPermissions(installDir)) {
      console.log(
        chalk.yellow(`⚠️  No write access to ${installDir}. Requesting sudo...`)
      );

      // Try to create directory with sudo
      const mkdirCommand = `mkdir -p ${installDir}`;
      if (!elevatePermissions(mkdirCommand)) {
        throw new Error(
          `Cannot create directory ${installDir}. Please check your permissions.`
        );
      }

      // Try to write file with sudo
      const tempFilePath = path.join(os.tmpdir(), "bismuthcli");
      fs.writeFileSync(tempFilePath, response.data, { mode: 0o755 });

      const sudoMoveCommand = `mv ${tempFilePath} ${binPath}`;
      if (!elevatePermissions(sudoMoveCommand)) {
        throw new Error(
          `Cannot move file to ${binPath}. Please check your permissions.`
        );
      }
    } else {
      // If we have permissions, proceed normally
      fs.mkdirSync(installDir, { recursive: true });
      fs.writeFileSync(binPath, response.data, { mode: 0o755 });
    }

    console.log(chalk.green(`✅ Installed Bismuth CLI to ${binPath}`));

    if (argv.quickstart) {
      await quickstart(binPath);
    }
  } catch (error: any) {
    console.error(chalk.red("❌ Installation failed:"), error.message);

    // Provide more detailed error guidance
    if (error.message.includes("permissions")) {
      console.log(
        chalk.yellow(
          "💡 Tip: Try running the installation with sudo or as an administrator."
        )
      );
    }
  }
}

async function quickstart(cliPath?: string) {
  console.log("First, let's log you in to the Bismuth platform.");

  const loginCmd = cliPath ? `${cliPath} login` : "biscli login";
  console.log(`Running: ${chalk.cyan(loginCmd)}`);

  child_process.execSync(loginCmd, { stdio: "inherit" });

  console.log("");
  const { useSampleProject } = await inquirer.prompt([
    {
      type: "confirm",
      name: "useSampleProject",
      message:
        "Would you like to use our sample project to start with? If not, you'll be able to pick any repository on your computer.",
      default: true,
    },
  ]);

  let repoPath: string;
  if (useSampleProject) {
    // Sample Project Walkthrough
    console.log("Cloning sample project...");
    const sampleRepoPath = "quickstart-sample";

    // Remove existing sample project if it exists
    if (fs.existsSync(sampleRepoPath)) {
      fs.rmSync(sampleRepoPath, { recursive: true, force: true });
    }

    child_process.execSync(
      `git clone --quiet https://github.com/BismuthCloud/quickstart-sample ${sampleRepoPath}`,
      { stdio: "inherit" }
    );

    console.log("");
    console.log("👉 First, import the repository to Bismuth");
    const importCmd = cliPath
      ? `${cliPath} import ${sampleRepoPath}`
      : `biscli import ${sampleRepoPath}`;
    console.log(`Running: ${chalk.cyan(importCmd)}`);
    await pressEnterToContinue();
    console.log("");

    child_process.execSync(importCmd, { stdio: "inherit" });

    repoPath = path.resolve(sampleRepoPath);

    console.log("");
    console.log(
      "👉 In another terminal, let's run the project to see what we're working with."
    );
    console.log(
      `cd to ${chalk.cyan(sampleRepoPath)} and run ${chalk.cyan(
        "npm i && npm run dev"
      )} and go to the URL.`
    );
    await pressEnterToContinue();

    console.log(
      "This is a simple TODO app that we'll have Bismuth extend for us."
    );
    console.log(
      "💡 Fun fact: Bismuth actually created this project from scratch in a single message!"
    );
    await pressEnterToContinue(
      "Once you've explored the app, kill the development server and press Enter to continue the guide."
    );
    console.log("");

    console.log("👉 Let's start chatting with Bismuth.");
    console.log("In your second terminal, open the chat interface:");
    const chatCmd = cliPath
      ? `${cliPath} chat --repo "${repoPath}"`
      : `biscli chat --repo "${repoPath}"`;
    console.log(chalk.cyan(chatCmd));
    await pressEnterToContinue();

    console.log(
      "We're first going to ask Bismuth to add a feature. Send this message:"
    );
    console.log(
      chalk.magenta(
        "Hey Bismuth, I need you to add the ability to set due dates on tasks. If a task is past its due date, it should be highlighted."
      )
    );
    console.log(
      "Bismuth will now plan out how to complete the task, collect relevant information from the repository, and finally begin working."
    );
    await pressEnterToContinue("Press Enter once Bismuth has finished.");
    console.log("");

    console.log(
      `👉 Bismuth is now showing you the diff of the code it wrote. Press ${chalk.yellow(
        "y"
      )} to accept the changes.`
    );
    console.log(
      `Now, let's check Bismuth's work. Hit ${chalk.yellow(
        "Esc"
      )} to exit the chat interface, run ${chalk.cyan(
        "npm run dev"
      )} again, and test the new date selection feature.`
    );
    console.log(
      "If there is an issue, just launch the chat again, describe the issue, and ask Bismuth to fix it!"
    );
    await pressEnterToContinue(
      "Once you're done, kill the development server and press Enter to continue."
    );
    console.log("");

    console.log(
      "👉 We're now going to have Bismuth fix an intentionally placed bug."
    );
    console.log(`Open ${chalk.cyan("src/App.tsx")} and delete the`);
    console.log("    saveTasks(updatedTasks);");
    console.log(`line in ${chalk.cyan("handleToggleTask")}.`);
    await pressEnterToContinue();

    console.log("Start the chat again, and send:");
    console.log(
      chalk.magenta(
        "It looks like task toggle state is not saved between page refreshes. Can you fix that?"
      )
    );
    await pressEnterToContinue("Press Enter once Bismuth has finished.");
    console.log("");

    console.log(
      `Examine the diff, press ${chalk.yellow(
        "y"
      )} to accept, and let's check Bismuth's work again.`
    );
    console.log(
      `Run ${chalk.cyan(
        "npm run dev"
      )} and make sure toggling a task completed is persisted across refreshes.`
    );
    await pressEnterToContinue();
    console.log("");

    console.log("👉 Finally, let's delete the project");
    const deleteCmd = cliPath
      ? `${cliPath} project delete ${sampleRepoPath}`
      : `biscli project delete ${sampleRepoPath}`;
    console.log(`Run ${chalk.cyan(deleteCmd)}`);
    await pressEnterToContinue();
    console.log("");

    console.log("🚀 And that's it!");
    console.log(
      `You can now import your own project with ${chalk.cyan(
        "biscli import {path}"
      )} and begin chatting!`
    );
    console.log(
      `💡 Use the '${chalk.cyan(
        "/help"
      )}' command in chat for more information, or '${chalk.cyan(
        "/feedback"
      )}' to send us feedback or report a bug.`
    );
  } else {
    // User's Own Project Walkthrough
    console.log("Let's import a project you'd like to work on.");

    const isGitRepo = fs.existsSync(path.join(process.cwd(), ".git"));

    if (isGitRepo) {
      const { useCurrentDir } = await inquirer.prompt([
        {
          type: "confirm",
          name: "useCurrentDir",
          message: "Would you like to use the current directory?",
          default: true,
        },
      ]);

      repoPath = useCurrentDir ? process.cwd() : await selectRepository();
    } else {
      repoPath = await selectRepository();
    }

    const importCmd = cliPath
      ? `${cliPath} import "${repoPath}"`
      : `biscli import "${repoPath}"`;
    console.log(chalk.cyan(`Running: ${importCmd}`));
    await pressEnterToContinue();

    child_process.execSync(importCmd, { stdio: "inherit" });

    console.log(chalk.green("🚀 Now you can start chatting!"));

    console.log(
      `💡 Use the '${chalk.cyan(
        "/help"
      )}' command in chat for more information, or '${chalk.cyan(
        "/feedback"
      )}' to send us feedback or report a bug.`
    );

    const chatCmd = cliPath
      ? `${cliPath} chat --repo "${repoPath}"`
      : `biscli chat --repo "${repoPath}"`;
    console.log(chalk.bold(chalk.cyan(`Running: ${chatCmd}`)));
    await pressEnterToContinue();

    child_process.execSync(chatCmd, { stdio: "inherit" });
  }
}

async function pressEnterToContinue(
  message: string = "Press Enter to continue..."
) {
  await inquirer.prompt([
    {
      type: "input",
      name: "continue",
      message: message,
    },
  ]);
}

async function selectRepository(): Promise<string> {
  while (true) {
    const { repoPath } = await inquirer.prompt([
      {
        type: "input",
        name: "repoPath",
        message: "Path to repository:",
        validate: (input) => {
          const fullPath = path.resolve(input);
          return fs.existsSync(path.join(fullPath, ".git"))
            ? true
            : "Not a git repository";
        },
      },
    ]);

    return path.resolve(repoPath);
  }
}

const parsed = yargs(hideBin(process.argv))
  .command(
    "install",
    "Install the Bismuth CLI",
    (yargs) => {
      return yargs
        .option("dir", {
          type: "string",
          description: "Directory to install the CLI",
          default: "/usr/local/bin/",
        })
        .option("cli-version", {
          type: "string",
          description: "Version to install",
          default: "LATEST",
        })
        .option("quickstart", {
          type: "boolean",
          description: "Run quickstart",
          default: true,
        });
    },
    installCli
  )
  .command("quickstart", "See how to use the Bismuth CLI", {}, () =>
    quickstart()
  )
  .strict()
  .demandCommand()
  .help()
  .parse();
