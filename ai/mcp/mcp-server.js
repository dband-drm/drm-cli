#!/usr/bin/env node
'use strict';

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const { loadDrmPath, executeTool, TOOL_SCHEMAS } = require('../lib/drm-helpers');

const TOOLS = TOOL_SCHEMAS.map(({ name, description, schema }) => ({ name, description, inputSchema: schema }));

function toolResult(text, isError = false) {
    return { content: [{ type: 'text', text }], isError };
}

async function main() {
    const server = new Server(
        { name: 'drm-cli', version: '1.0.0' },
        { capabilities: { tools: {} } }
    );

    server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: input = {} } = request.params;
        const { output, isError } = executeTool(name, input, loadDrmPath());
        return toolResult(output, isError);
    });

    const transport = new StdioServerTransport();
    await server.connect(transport);
}

main().catch((err) => {
    process.stderr.write(`MCP server error: ${err.message}\n`);
    process.exit(1);
});
