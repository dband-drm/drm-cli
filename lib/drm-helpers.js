'use strict';

const { spawnSync } = require('child_process');
const { readFileSync } = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_FILE = path.join(os.homedir(), '.drm-cli.json');
const SCRIPT_DIR = path.join(__dirname, '..');
const python = os.platform() === 'win32' ? 'python' : 'python3';
const ANSI_RE = /\x1b\[[0-9;]*m/g;

const DB_SCRIPT = [
    'import sqlite3,json,sys',
    'conn=sqlite3.connect(sys.argv[1])',
    'conn.row_factory=sqlite3.Row',
    'rows=conn.execute(sys.argv[2]).fetchall()',
    'print(json.dumps([dict(r) for r in rows]))',
    'conn.close()'
].join('\n');

// Combined query for drm_status — single spawn instead of two
const STATUS_SCRIPT = [
    'import sqlite3,json,sys',
    'conn=sqlite3.connect(sys.argv[1])',
    'conn.row_factory=sqlite3.Row',
    "c=dict(conn.execute('SELECT (SELECT COUNT(*) FROM releases WHERE is_active=1) as r,(SELECT COUNT(*) FROM connections WHERE is_active=1) as c').fetchone())",
    "recent=[dict(x) for x in conn.execute('SELECT r.name as release,c.name as connection,d.start_time,ds.name as status FROM deployments d JOIN releases r ON r.id=d.release_id JOIN connections c ON c.id=d.connection_id JOIN deployment_statuses ds ON ds.id=d.deployment_status_id ORDER BY d.start_time DESC LIMIT 5').fetchall()]",
    "print(json.dumps({'counts':c,'recent':recent}))",
    'conn.close()'
].join('\n');

function stripAnsi(str) {
    return (str || '').replace(ANSI_RE, '');
}

function loadDrmPath() {
    try {
        return JSON.parse(readFileSync(CONFIG_FILE, 'utf-8')).drm_path || null;
    } catch (_) {
        return null;
    }
}

function loadDrmConfig(drmPath) {
    try {
        return JSON.parse(readFileSync(path.join(drmPath, 'drm_deploy.config'), 'utf-8'));
    } catch (_) {
        return {};
    }
}

function runDrmCli(args) {
    const result = spawnSync('node', [path.join(SCRIPT_DIR, 'index.js'), ...args], {
        stdio: 'pipe',
        encoding: 'utf-8'
    });
    return {
        output: stripAnsi((result.stdout || '') + (result.stderr || '')),
        isError: (result.status ?? 1) !== 0
    };
}

function queryDb(drmPath, sql) {
    const cfg = loadDrmConfig(drmPath);
    const c = cfg.config || {};
    const dbName = `${c.db_file_name || 'drm_db'}.${c.sqlite_file_ext || 'sqlite'}`;
    const dbFile = path.join(drmPath, 'db', dbName);
    const result = spawnSync(python, ['-c', DB_SCRIPT, dbFile, sql], {
        stdio: 'pipe',
        encoding: 'utf-8'
    });
    const isError = (result.status ?? 1) !== 0;
    return {
        output: isError
            ? stripAnsi(result.stderr || 'SQLite query failed')
            : stripAnsi((result.stdout || '').trim()),
        isError
    };
}

// Read the JSON DB file for json-type installs
function loadJsonDb(drmPath, cfg) {
    const c = cfg.config || {};
    const fname = `${c.db_file_name || 'drm_db'}.${c.data_file_ext || 'json'}`;
    try {
        return JSON.parse(readFileSync(path.join(drmPath, 'db', fname), 'utf-8'));
    } catch (_) {
        return null;
    }
}

function buildStatus(drmPath) {
    const cfg = loadDrmConfig(drmPath);
    const info = cfg.installation_info || {};
    const isSqlite = (info.installation_type || 'sqlite') === 'sqlite';
    const lines = [
        `DRM Path:           ${drmPath}`,
        `Version:            ${cfg.drm_version || 'unknown'}`,
        `Install Type:       ${info.installation_type || 'unknown'}`,
        `DB Secured:         ${info.db_secured ?? 'unknown'}`
    ];

    if (isSqlite) {
        const result = spawnSync(python, ['-c', STATUS_SCRIPT, path.join(drmPath, 'db', 'drm_db.sqlite')], {
            stdio: 'pipe',
            encoding: 'utf-8'
        });
        if ((result.status ?? 1) === 0) {
            try {
                const { counts, recent } = JSON.parse(stripAnsi((result.stdout || '').trim()));
                lines.push(`Active Releases:    ${counts.r}`);
                lines.push(`Active Connections: ${counts.c}`);
                if (recent.length) {
                    lines.push('\nLast Deployments:');
                    recent.forEach(r => lines.push(`  [${r.status}] ${r.release} -> ${r.connection}  (${r.start_time})`));
                }
            } catch (_) {}
        }
    } else {
        const db = loadJsonDb(drmPath, cfg);
        if (db) {
            const releases = (db.releases || []).filter(r => r.is_active !== false);
            const connCount = releases.reduce((n, r) => n + (r.solutions || []).reduce((m, s) => m + (s.connections || []).length, 0), 0);
            lines.push(`Active Releases:    ${releases.length}`);
            lines.push(`Active Connections: ${connCount}`);
            lines.push('(Deployment history not available for json installs)');
        }
    }
    return { output: lines.join('\n'), isError: false };
}

function listReleasesJson(drmPath, cfg) {
    const db = loadJsonDb(drmPath, cfg);
    if (!db) return { output: 'Could not read JSON DB file.', isError: true };
    const rows = (db.releases || []).map(r => ({ id: r.id, name: r.name, is_active: r.is_active !== false }));
    return { output: JSON.stringify(rows), isError: false };
}

function listConnectionsJson(drmPath, cfg) {
    const db = loadJsonDb(drmPath, cfg);
    if (!db) return { output: 'Could not read JSON DB file.', isError: true };
    const rows = [];
    for (const r of (db.releases || [])) {
        for (const s of (r.solutions || [])) {
            for (const c of (s.connections || [])) {
                rows.push({ id: rows.length + 1, name: c.name, release: r.name, is_active: true });
            }
        }
    }
    return { output: JSON.stringify(rows), isError: false };
}

function executeTool(name, input, drmPath) {
    if (!drmPath && name !== 'drm_install') {
        return { output: 'DRM not installed. Run drm_install first.', isError: true };
    }
    if (name === 'drm_status') {
        return buildStatus(drmPath);
    }

    if (name === 'drm_list_releases' || name === 'drm_list_connections') {
        const cfg = loadDrmConfig(drmPath);
        const isSqlite = ((cfg.installation_info || {}).installation_type || 'sqlite') === 'sqlite';
        if (name === 'drm_list_releases') {
            return isSqlite
                ? queryDb(drmPath, 'SELECT id, name, is_active FROM releases ORDER BY id')
                : listReleasesJson(drmPath, cfg);
        }
        return isSqlite
            ? queryDb(drmPath, 'SELECT id, name, is_active FROM connections ORDER BY id')
            : listConnectionsJson(drmPath, cfg);
    }
    if (name === 'drm_dryrun' || name === 'drm_deploy' || name === 'drm_align') {
        const args = ['deploy', '-c', input.connection, '-r', input.release];
        const key = input.key || process.env.DRM_SECRET;
        if (key) args.push('-p', key);
        args.push(name === 'drm_dryrun' ? '--dryrun' : name === 'drm_deploy' ? '--deploy' : '--align');
        return runDrmCli(args);
    }
    if (name === 'drm_install') {
        const args = ['install', '-f', input.path, '-d', input.type];
        if (input.key) args.push('-p', input.key);
        return runDrmCli(args);
    }
    if (name === 'drm_crypto_encrypt') {
        return runDrmCli(['crypto', '--encrypt', '-t', input.text, '-p', input.key]);
    }
    return { output: `Unknown tool: ${name}`, isError: true };
}

// Base tool schemas — applied with inputSchema (MCP) or input_schema (Anthropic) by each consumer
const TOOL_SCHEMAS = [
    {
        name: 'drm_status',
        description: 'Show DRM installation status: path, version, install type, release and connection counts, last 5 deployments.',
        schema: { type: 'object', properties: {}, required: [] }
    },
    {
        name: 'drm_list_releases',
        description: 'List all releases in the DRM database.',
        schema: { type: 'object', properties: {}, required: [] }
    },
    {
        name: 'drm_list_connections',
        description: 'List all connections defined in the DRM database.',
        schema: { type: 'object', properties: {}, required: [] }
    },
    {
        name: 'drm_dryrun',
        description: 'Run a DRM dryrun (generates scripts without executing) for a given connection and release.',
        schema: {
            type: 'object',
            properties: {
                connection: { type: 'string', description: 'DRM connection name' },
                release:    { type: 'string', description: 'Release ID or name' },
                key:        { type: 'string', description: 'Encryption key (optional, or set DRM_SECRET env var)' }
            },
            required: ['connection', 'release']
        }
    },
    {
        name: 'drm_deploy',
        description: 'Run a full DRM deployment. Always run drm_dryrun first unless the user explicitly skips it.',
        schema: {
            type: 'object',
            properties: {
                connection: { type: 'string', description: 'DRM connection name' },
                release:    { type: 'string', description: 'Release ID or name' },
                key:        { type: 'string', description: 'Encryption key (optional)' }
            },
            required: ['connection', 'release']
        }
    },
    {
        name: 'drm_align',
        description: 'Run DRM align (synchronises DB state without deploying) for a given connection and release.',
        schema: {
            type: 'object',
            properties: {
                connection: { type: 'string', description: 'DRM connection name' },
                release:    { type: 'string', description: 'Release ID or name' },
                key:        { type: 'string', description: 'Encryption key (optional)' }
            },
            required: ['connection', 'release']
        }
    },
    {
        name: 'drm_install',
        description: 'Install DRM to a target path.',
        schema: {
            type: 'object',
            properties: {
                path: { type: 'string', description: 'Absolute path to install DRM into' },
                type: { type: 'string', enum: ['sqlite', 'json'], description: 'DRM DB backend type' },
                key:  { type: 'string', description: 'Encryption key (optional)' }
            },
            required: ['path', 'type']
        }
    },
    {
        name: 'drm_crypto_encrypt',
        description: 'Encrypt a text phrase using the DRM encryption key.',
        schema: {
            type: 'object',
            properties: {
                text: { type: 'string', description: 'Text to encrypt' },
                key:  { type: 'string', description: 'Encryption key' }
            },
            required: ['text', 'key']
        }
    }
];

module.exports = { loadDrmPath, executeTool, TOOL_SCHEMAS };

