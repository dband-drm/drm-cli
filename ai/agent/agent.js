#!/usr/bin/env node
'use strict';

const Anthropic = require('@anthropic-ai/sdk');
const { loadDrmPath, executeTool, TOOL_SCHEMAS } = require('../lib/drm-helpers');

const MAX_TURNS = 10;
const MODEL = 'claude-sonnet-4-6';

const DRM_TOOLS = TOOL_SCHEMAS.map(({ name, description, schema }) => ({ name, description, input_schema: schema }));

async function runAgent(userMessage) {
    if (!process.env.ANTHROPIC_API_KEY) {
        console.error('Error: ANTHROPIC_API_KEY environment variable is not set.');
        process.exit(1);
    }

    const drmPath = loadDrmPath();
    const systemPrompt = `You are a DRM (Data Release Management) assistant. You help users manage database releases using the DRM-CLI tool.

${drmPath ? `Installed DRM path: ${drmPath}` : 'DRM is not installed yet.'}

Guidelines:
- Always run drm_dryrun before drm_deploy and show the output to the user, unless they explicitly say to skip it.
- If a tool call fails, show the error clearly and suggest a fix.
- When listing releases or connections, format the output as a readable table.
- If an encryption key is needed, mention that DRM_SECRET env var can be set to avoid passing it explicitly.
- Be concise and action-oriented.`;

    const client = new Anthropic.default();
    const messages = [{ role: 'user', content: userMessage }];
    let turns = 0;

    while (turns++ < MAX_TURNS) {
        const response = await client.messages.create({
            model: MODEL,
            max_tokens: 4096,
            system: systemPrompt,
            tools: DRM_TOOLS,
            messages
        });

        messages.push({ role: 'assistant', content: response.content });

        for (const block of response.content) {
            if (block.type === 'text' && block.text) process.stdout.write(block.text + '\n');
        }

        if (response.stop_reason === 'end_turn') break;

        if (response.stop_reason === 'tool_use') {
            const toolResults = [];
            for (const block of response.content) {
                if (block.type !== 'tool_use') continue;
                process.stderr.write(`[tool] ${block.name}(${JSON.stringify(block.input)})\n`);
                const result = executeTool(block.name, block.input, drmPath);
                if (result.isError) process.stderr.write(`[tool error] ${result.output}\n`);
                toolResults.push({
                    type: 'tool_result',
                    tool_use_id: block.id,
                    content: result.output,
                    is_error: result.isError
                });
            }
            messages.push({ role: 'user', content: toolResults });
        } else {
            break;
        }
    }

    if (turns >= MAX_TURNS) console.error(`\nReached max turns limit (${MAX_TURNS}). Stopping.`);
}

const userPrompt = process.argv.slice(2).join(' ').trim();
if (!userPrompt) {
    console.error('Usage: node ai/agent/agent.js "<natural language command>"');
    console.error('Example: node ai/agent/agent.js "list all releases"');
    process.exit(1);
}

runAgent(userPrompt).catch((err) => {
    console.error(`Agent error: ${err.message}`);
    process.exit(1);
});
