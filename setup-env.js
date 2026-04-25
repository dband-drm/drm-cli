const { spawnSync } = require('child_process');
const os = require('os');

const isWin = os.platform() === 'win32';
const python = isWin ? 'python' : 'python3';

console.log(`--- Detecting OS: ${os.platform()} ---`);

// Verify Python is available
const check = spawnSync(python, ['--version']);
if (check.error) {
    console.error(`Error: ${python} not found. Please install Python >= 3.10`);
    process.exit(1);
}

// Forward any extra args to install.py (e.g. -f /path -d sqlite -p mykey)
const args = process.argv.slice(2);

// Run DRM installer with full stdio inheritance for interactive prompts
console.log('Running DRM installer...');
const result = spawnSync(python, ['install.py', ...args], { stdio: 'inherit' });
process.exit(result.status ?? 1);

