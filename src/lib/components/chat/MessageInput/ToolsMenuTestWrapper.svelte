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

	let previousReasoningEffort = undefined;
	let previousTemperature = undefined;
	let extendedThinkingWasEnabled = false;

	$: if (extendedThinkingEnabled) {
		previousReasoningEffort = params.reasoning_effort;
		previousTemperature = params.temperature;
		params = { ...params, reasoning_effort: 'high', temperature: 1 };
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
		params = newParams;
		previousReasoningEffort = undefined;
		previousTemperature = undefined;
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
