<script lang="ts">
  import ToolsMenu from './ToolsMenu.svelte';
  export let selectedToolIds: string[] = [];
export let webSearchEnabled = false;
export let codeInterpreterEnabled = false;
export let imageGenerationEnabled = false;
export let extendedThinkingEnabled = false;
export let reasoningCapable = true;
export let onClose: Function = () => {};
export let params = {};
export let selectedModels: string[] = [];

let previousReasoningEffort = undefined;
let previousStreamResponse = undefined;
let previousThinking = undefined;
let previousSelectedModels = undefined;

$: if (extendedThinkingEnabled) {
        previousReasoningEffort = params.reasoning_effort;
        previousStreamResponse = params.stream_response;
        previousThinking = params.thinking;
        previousSelectedModels = [...selectedModels];
        params = {
                ...params,
                stream_response: true,
                thinking: { type: 'enabled', budget_tokens: 5000 },
                reasoning_effort: 'high'
        };
        selectedModels = ['claude'];
} else if (
        'reasoning_effort' in params ||
        'stream_response' in params ||
        'thinking' in params ||
        previousSelectedModels !== undefined
) {
        if ('reasoning_effort' in params) {
                if (previousReasoningEffort !== undefined) {
                        params = { ...params, reasoning_effort: previousReasoningEffort };
                } else {
                        const { reasoning_effort, ...rest } = params;
                        params = rest;
                }
                previousReasoningEffort = undefined;
        }
        if ('stream_response' in params) {
                if (previousStreamResponse !== undefined) {
                        params = { ...params, stream_response: previousStreamResponse };
                } else {
                        const { stream_response, ...rest } = params;
                        params = rest;
                }
                previousStreamResponse = undefined;
        }
        if ('thinking' in params) {
                if (previousThinking !== undefined) {
                        params = { ...params, thinking: previousThinking };
                } else {
                        const { thinking, ...rest } = params;
                        params = rest;
                }
                previousThinking = undefined;
        }
        if (previousSelectedModels !== undefined) {
                selectedModels = previousSelectedModels;
                previousSelectedModels = undefined;
        }
}
</script>

<ToolsMenu
bind:selectedToolIds
bind:webSearchEnabled
bind:codeInterpreterEnabled
bind:imageGenerationEnabled
bind:extendedThinkingEnabled
{reasoningCapable}
{onClose}
>
  <button>open</button>
</ToolsMenu>
