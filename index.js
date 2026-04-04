#!/usr/bin/env node

const { spawnSync } = require('child_process');
const os = require('os');
const path = require('path');
const fs = require('fs');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const isWin = os.platform() === 'win32';
const python = isWin ? 'python' : 'python3';
const CONFIG_FILE = path.join(os.homedir(), '.drm-cli.json');
const SCRIPT_DIR = __dirname;

function saveInstallPath(drm_path) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify({ drm_path }, null, 2));
}

function loadInstallPath() {
    if (!fs.existsSync(CONFIG_FILE)) {
        console.error('Error: DRM not installed. Run "drm-cli install" first.');
        process.exit(1);
    }
    return JSON.parse(fs.readFileSync(CONFIG_FILE)).drm_path;
}

function run(cwd, script, args) {
    const result = spawnSync(python, [script, ...args], { cwd, stdio: 'inherit' });
    process.exit(result.status ?? 1);
}

yargs(hideBin(process.argv))

    .command(
        'install',
        'Install DRM to a target path',
        (y) => y
            .option('f', { alias: 'path',         describe: 'Install path',       type: 'string' })
            .option('d', { alias: 'type',         describe: 'DB type: sqlite|json', type: 'string' })
            .option('p', { alias: 'key',          describe: 'Encryption key',     type: 'string' })
            .option('trace',                      { describe: 'Debug logging',    type: 'boolean' }),
        (argv) => {
            const args = [];
            if (argv.f) { args.push('-f', argv.f); saveInstallPath(argv.f); }
            if (argv.d) args.push('-d', argv.d);
            if (argv.p) args.push('-p', argv.p);
            if (argv.trace) args.push('--trace');
            run(SCRIPT_DIR, 'install.py', args);
        }
    )

    .command(
        'deploy',
        'Deploy a release',
        (y) => y
            .option('c', { alias: 'connection',   describe: 'Connection name',    type: 'string', demandOption: true })
            .option('r', { alias: 'release',      describe: 'Release ID',         type: 'string', demandOption: true })
            .option('p', { alias: 'key',          describe: 'Encryption key',     type: 'string' })
            .option('dryrun',                     { describe: 'Generate scripts only',  type: 'boolean' })
            .option('deploy',                     { describe: 'Generate and execute',   type: 'boolean' })
            .option('align',                      { describe: 'Align DB',               type: 'boolean' })
            .option('trace',                      { describe: 'Debug logging',    type: 'boolean' })
            .option('f', { alias: 'path',         describe: 'DRM path (overrides saved path)', type: 'string' }),
        (argv) => {
            const drm_path = argv.f || loadInstallPath();
            const args = ['-c', argv.c, '-r', argv.r];
            if (argv.p)      args.push('-p', argv.p);
            if (argv.dryrun) args.push('--dryrun');
            if (argv.deploy) args.push('--deploy');
            if (argv.align)  args.push('--align');
            if (argv.trace)  args.push('--trace');
            run(drm_path, 'drm_deploy.py', args);
        }
    )

    .command(
        'crypto',
        'Encrypt text or change encryption key',
        (y) => y
            .option('encrypt',        { describe: 'Encrypt a text phrase',         type: 'boolean' })
            .option('changepassword', { describe: 'Change the encryption key',      type: 'boolean' })
            .option('p', { alias: 'key',    describe: 'Current encryption key',    type: 'string' })
            .option('n', { alias: 'newkey', describe: 'New encryption key',        type: 'string' })
            .option('t', { alias: 'text',   describe: 'Text to encrypt',           type: 'string' })
            .option('trace',                { describe: 'Debug logging',           type: 'boolean' })
            .option('f', { alias: 'path',   describe: 'DRM path (overrides saved path)', type: 'string' }),
        (argv) => {
            const drm_path = argv.f || loadInstallPath();
            const args = [];
            if (argv.encrypt)        args.push('--encrypt');
            if (argv.changepassword) args.push('--changepassword');
            if (argv.p) args.push('-p', argv.p);
            if (argv.n) args.push('-n', argv.n);
            if (argv.t) args.push('-t', argv.t);
            if (argv.trace) args.push('--trace');
            run(drm_path, 'drm_crypto.py', args);
        }
    )

    .command(
        'uninstall',
        'Uninstall DRM from the installed path',
        (y) => y
            .option('f', { alias: 'path',   describe: 'DRM path (overrides saved path)', type: 'string' })
            .option('p', { alias: 'key',    describe: 'Encryption key',    type: 'string' })
            .option('F', { alias: 'force',  describe: 'Skip confirmation', type: 'boolean' })
            .option('trace',                { describe: 'Debug logging',   type: 'boolean' }),
        (argv) => {
            const drm_path = argv.f || loadInstallPath();
            const args = ['-f', drm_path];
            if (argv.p)     args.push('-p', argv.p);
            if (argv.F)     args.push('--F');
            if (argv.trace) args.push('--trace');
            // Remove saved config after uninstall
            run(SCRIPT_DIR, 'uninstall.py', args);
            if (fs.existsSync(CONFIG_FILE)) fs.unlinkSync(CONFIG_FILE);
        }
    )

    .demandCommand(1, 'Please specify a command: install | deploy | crypto | uninstall')
    .help()
    .parse();
