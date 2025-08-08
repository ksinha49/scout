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
        let previousTemperature = undefined;
        let previousStreamResponse = undefined;
        let previousThinking = undefined;
        let previousSelectedModels: string[] = [];
        let extendedThinkingWasEnabled = false;

        $: if (extendedThinkingEnabled) {
                previousReasoningEffort = params.reasoning_effort;
                previousTemperature = params.temperature;
                previousStreamResponse = params.stream_response;
                previousThinking = params.thinking;
                previousSelectedModels = [...selectedModels];
                params = {
                        ...params,
                        reasoning_effort: 'high',
                        temperature: 1,
                        stream_response: true,
                        thinking: { type: 'enabled', budget_tokens: 5000 }
                };
                selectedModels = ['claude'];
                extendedThinkingWasEnabled = true;
        } else if (extendedThinkingWasEnabled) {
                let newParams = { ...params };
                if (previousReasoningEffort !== undefined) {
                        newParams.reasoning_effort = previousReasoningEffort;
                } else {
                        delete newParams.reasoning_effort;
                }
                if (previousTemperature !== undefined) {
                        newParams.temperature = previousTemperature;
                } else {
                        delete newParams.temperature;
                }
                if (previousStreamResponse !== undefined) {
                        newParams.stream_response = previousStreamResponse;
                } else {
                        delete newParams.stream_response;
                }
                if (previousThinking !== undefined) {
                        newParams.thinking = previousThinking;
                } else {
                        delete newParams.thinking;
                }
                params = newParams;
                selectedModels = previousSelectedModels;
                previousReasoningEffort = undefined;
                previousTemperature = undefined;
                previousStreamResponse = undefined;
                previousThinking = undefined;
                previousSelectedModels = [];
                extendedThinkingWasEnabled = false;
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
