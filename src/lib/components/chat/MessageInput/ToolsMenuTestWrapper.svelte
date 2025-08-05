<script lang="ts">
  import ToolsMenu from './ToolsMenu.svelte';
  export let selectedToolIds: string[] = [];
  export let webSearchEnabled = false;
  export let codeInterpreterEnabled = false;
  export let imageGenerationEnabled = false;
  export let onClose: Function = () => {};
</script>

<ToolsMenu
  bind:selectedToolIds
  bind:webSearchEnabled
  bind:codeInterpreterEnabled
  bind:imageGenerationEnabled
  {onClose}
>
  <button>open</button>
</ToolsMenu>
