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

async function installCli(argv: any) {
  console.log(chalk.magenta(LOGO));
  console.log();

  const version =
    argv.cliVersion === "LATEST"
      ? await axios
          .get("https://bismuthcloud.github.io/cli/LATEST")
          .then((r) => r.data.trim())
      : argv.cliVersion;

  const installDir = path.resolve(argv.dir);
  const binPath = path.join(installDir, "biscli");

  console.log(`Installing Bismuth CLI ${version} to ${installDir}`);

  const triple = getPlatformTriple();
  const downloadUrl = `https://github.com/BismuthCloud/cli/releases/download/v${version}/bismuthcli.${triple}`;

  const response = await axios({
    method: "get",
    url: downloadUrl,
    responseType: "arraybuffer",
  });

  fs.mkdirSync(installDir, { recursive: true });
  fs.writeFileSync(binPath, response.data, { mode: 0o755 });

  console.log(chalk.green(`✅ Installed Bismuth CLI to ${binPath}`));

  const not_in_path = !(process.env.PATH || "").split(":")
    .map((p) => path.resolve(p))
    .includes(path.resolve(installDir));

  if (not_in_path) {
    console.log(
      chalk.yellow(
        `⚠️ ${installDir} is not in your $PATH - you'll need to add it to your shell rc`
      )
    );
  }

  console.log(chalk.green(`✅ Installed Bismuth CLI to ${binPath}`));

  if (argv.quickstart) {
      await quickstart(not_in_path ? binPath : undefined);
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
        "Would you like to first go through a guided tour with a sample project?",
      default: true,
    },
  ]);

  let repoPath: string;
  if (useSampleProject) {
    console.log(
      "Great! You'll be able to import your own project after this tour."
    );

    console.log("Cloning sample project...");
    const sampleRepoPath = "quickstart-sample";

    if (fs.existsSync(sampleRepoPath)) {
      fs.rmSync(sampleRepoPath, { recursive: true, force: true });
    }

    child_process.execSync(
      `git clone --quiet https://github.com/BismuthCloud/quickstart-sample ${sampleRepoPath}`,
      { stdio: "inherit" }
    );
    console.log("");

    console.log(
      "👉 In another terminal, let's run the project to see what we're working with."
    );
    console.log(
      `Run ${chalk.cyan(
        `cd ${sampleRepoPath} && npm -i && npm run dev`
      )} and go to the URL`
    );
    await pressEnterToContinue();

    console.log(
      "This is a simple TODO app that we'll have Bismuth extend for us."
    );
    console.log(
      "💡 Fun fact: Bismuth actually created this project from scratch in a single message!"
    );
    await pressEnterToContinue();
    console.log("");

    console.log("👉 First, let's import the repository to Bismuth");
    const importCmd = cliPath
      ? `${cliPath} import ${sampleRepoPath}`
      : `biscli import ${sampleRepoPath}`;
    console.log(`Running: ${chalk.cyan(importCmd)}`);
    await pressEnterToContinue();
    child_process.execSync(importCmd + " --upload", { stdio: "inherit" });
    console.log("");

    repoPath = path.resolve(sampleRepoPath);

    console.log("👉 Now let's start chatting with Bismuth.");
    console.log("In another terminal, open the chat interface:");
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
        "Hey Bismuth, I need you to add the ability to set due dates on tasks. The date set on a task should be shown in a smaller font and must be on a new line below the title. If a task is past its due date, the task title should be shown in red. Also make sure the date selection box is the same height as the title input and has the same padding."
      )
    );
    console.log(
      "Bismuth will now plan out how to complete the task, collect relevant information from the repository, and finally begin working."
    );
    await pressEnterToContinue(
      "Press Enter once Bismuth is showing you a diff."
    );
    console.log("");

    console.log(
      `👉 Bismuth is now showing you the diff of the code it wrote. Press ${chalk.yellow(
        "y"
      )} to accept the changes.`
    );
    console.log(
      `Now, let's check Bismuth's work. Go back to the running app, refresh the page, and test the new date selection feature.`
    );
    console.log("If there is an issue, just ask Bismuth to fix it!");
    await pressEnterToContinue();
    console.log("");

    console.log("👉 Now let's have Bismuth fix an intentionally placed bug.");
    console.log(`Open ${chalk.cyan("src/App.tsx")} and delete the`);
    console.log("    saveTasks(updatedTasks);");
    console.log(`line in ${chalk.cyan("handleToggleTask")}.`);
    await pressEnterToContinue();

    console.log("Now tell Bismuth:");
    console.log(
      chalk.magenta(
        "It looks like task toggle state is not saved between page refreshes. Can you double check the saving logic in App.tsx?"
      )
    );
    await pressEnterToContinue(
      "Press Enter once Bismuth is showing you the diff."
    );
    console.log("");

    console.log(
      `Examine the diff, press ${chalk.yellow(
        "y"
      )} to accept, and check Bismuth's work again. Go back to the app, refresh, and ensure that marking a task done is persisted between refreshes.`
    );
    await pressEnterToContinue();
    console.log("");

    console.log("👉 Finally, let's clean up the project.");
    const deleteCmd = cliPath
      ? `${cliPath} project delete ${sampleRepoPath}`
      : `biscli project delete ${sampleRepoPath}`;
    console.log(
      `Exit the Bismuth chat interface by hitting ${chalk.yellow(
        "Esc"
      )}, kill the node development server, and run ${chalk.cyan(
        deleteCmd
      )} to delete the project from Bismuth.`
    );
    await pressEnterToContinue();
    console.log("");

    console.log("🚀 And that's it!");
    console.log("Bismuth can be used on much more than JavaScript frontends.");
    console.log(
      "Use it to refactor Java webservers, write Python backends, or even create utility programs in C."
    );
    console.log("Now let's pick one of your projects to work on.");
  } else {
    console.log("Let's import a project you'd like to work on.");
  }

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

  if (!useSampleProject) {
    console.log(chalk.green("🚀 Now you can start chatting!"));
  }

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

yargs(hideBin(process.argv))
  .command(
    "install",
    "Install the Bismuth CLI",
    (yargs) => {
      const defaultDir = fs.existsSync(path.join(os.homedir(), "bin"))
        ? path.join(os.homedir(), "bin")
        : path.join(os.homedir(), ".local/bin");
      return yargs
        .option("dir", {
          type: "string",
          description: "Directory to install the CLI",
          default: defaultDir,
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
