<script lang="ts">
    import { DropdownMenu } from 'bits-ui';
    import { flyAndScale } from '$lib/utils/transitions';
    import { getContext, tick } from 'svelte';

    import { config, user, tools as _tools } from '$lib/stores';
    import { getTools } from '$lib/apis/tools';

    import Dropdown from '$lib/components/common/Dropdown.svelte';
    import Tooltip from '$lib/components/common/Tooltip.svelte';

    import WrenchSolid from '$lib/components/icons/WrenchSolid.svelte';
    import GlobeAltSolid from '$lib/components/icons/GlobeAltSolid.svelte';
    import CommandLineSolid from '$lib/components/icons/CommandLineSolid.svelte';
    import PhotoSolid from '$lib/components/icons/PhotoSolid.svelte';
    import Check from '$lib/components/icons/Check.svelte';

    const i18n = getContext('i18n');

    export let selectedToolIds: string[] = [];
    export let webSearchEnabled = false;
    export let codeInterpreterEnabled = false;
    export let imageGenerationEnabled = false;

    export let onClose: Function;

    let show = false;
    let tools = {};

    $: if (show) {
        init();
    }

    const init = async () => {
        if ($_tools === null) {
            await _tools.set(await getTools(localStorage.token));
        }

        tools = $_tools.reduce((a, tool) => {
            a[tool.id] = {
                name: tool.name,
                description: tool.meta.description,
                enabled: selectedToolIds.includes(tool.id)
            };
            return a;
        }, {});
    };
</script>

<Dropdown
    bind:show
    on:change={(e) => {
        if (e.detail === false) {
            onClose?.();
        }
    }}
>
    <Tooltip content={$i18n.t('Tools')}>
        <slot />
    </Tooltip>

    <div slot="content">
        <DropdownMenu.Content
            class="w-full max-w-[200px] rounded-xl px-1 py-1 border border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-sm"
            sideOffset={10}
            alignOffset={-8}
            side="top"
            align="start"
            transition={flyAndScale}
        >
            {#if Object.keys(tools).length > 0}
                <div class="max-h-28 overflow-y-auto scrollbar-hidden">
                    {#each Object.keys(tools) as toolId}
                        <DropdownMenu.Item
                            class="flex w-full justify-between gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
                            on:click={async (e) => {
                                e.preventDefault();
                                tools[toolId].enabled = !tools[toolId].enabled;
                                await tick();
                                if (tools[toolId].enabled) {
                                    selectedToolIds = [...selectedToolIds, toolId];
                                } else {
                                    selectedToolIds = selectedToolIds.filter((id) => id !== toolId);
                                }
                            }}
                        >
                            <Tooltip
                                content={tools[toolId]?.description ?? ''}
                                placement="top-start"
                                className="flex flex-1 gap-2 items-center truncate"
                            >
                                <div class="shrink-0">
                                    <WrenchSolid />
                                </div>
                                <div class="truncate">{tools[toolId].name}</div>
                            </Tooltip>
                            {#if tools[toolId].enabled}
                                <Check className="shrink-0" />
                            {/if}
                        </DropdownMenu.Item>
                    {/each}
                </div>
                <hr class="border-black/5 dark:border-white/5 my-1" />
            {/if}

            {#if $config?.features?.enable_web_search && ($user.role === 'admin' || $user?.permissions?.features?.web_search)}
                <DropdownMenu.Item
                    class="flex w-full justify-between gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
                    on:click={(e) => {
                        e.preventDefault();
                        webSearchEnabled = !webSearchEnabled;
                    }}
                >
                    <div class="flex gap-2 items-center">
                        <GlobeAltSolid />
                        <div>{$i18n.t('Web Search')}</div>
                    </div>
                    {#if webSearchEnabled}
                        <Check className="shrink-0" />
                    {/if}
                </DropdownMenu.Item>
            {/if}

            {#if $config?.features?.enable_code_interpreter && ($user.role === 'admin' || $user?.permissions?.features?.code_interpreter)}
                <DropdownMenu.Item
                    class="flex w-full justify-between gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
                    on:click={(e) => {
                        e.preventDefault();
                        codeInterpreterEnabled = !codeInterpreterEnabled;
                    }}
                >
                    <div class="flex gap-2 items-center">
                        <CommandLineSolid />
                        <div>{$i18n.t('Code Interpreter')}</div>
                    </div>
                    {#if codeInterpreterEnabled}
                        <Check className="shrink-0" />
                    {/if}
                </DropdownMenu.Item>
            {/if}

            {#if $config?.features?.enable_image_generation && ($user.role === 'admin' || $user?.permissions?.features?.image_generation)}
                <DropdownMenu.Item
                    class="flex w-full justify-between gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl"
                    on:click={(e) => {
                        e.preventDefault();
                        imageGenerationEnabled = !imageGenerationEnabled;
                    }}
                >
                    <div class="flex gap-2 items-center">
                        <PhotoSolid />
                        <div>{$i18n.t('Image')}</div>
                    </div>
                    {#if imageGenerationEnabled}
                        <Check className="shrink-0" />
                    {/if}
                </DropdownMenu.Item>
            {/if}
        </DropdownMenu.Content>
    </div>
</Dropdown>

