<script lang="ts">
        import { onMount, getContext } from 'svelte';
        import { getPromptOptimizerConfig, setPromptOptimizerConfig } from '$lib/apis/configs';
        import { models } from '$lib/stores';

        import Switch from '$lib/components/common/Switch.svelte';
        import Textarea from '$lib/components/common/Textarea.svelte';

        const i18n = getContext('i18n');

        export let saveHandler: Function;

        let config = null;

        const submitHandler = async () => {
                const res = await setPromptOptimizerConfig(localStorage.token, config);
        };

        onMount(async () => {
                const res = await getPromptOptimizerConfig(localStorage.token);

                if (res) {
                        config = res;
                }
        });
</script>

<form
        class="flex flex-col h-full justify-between space-y-3 text-sm"
        on:submit|preventDefault={async () => {
                await submitHandler();
                saveHandler();
        }}
>
        <div class=" space-y-3 overflow-y-scroll scrollbar-hidden h-full">
                {#if config}
                        <div>
                                <div class="mb-3.5">
                                        <div class=" mb-2.5 text-base font-medium">{$i18n.t('Prompt Optimization')}</div>

                                        <hr class=" border-gray-100 dark:border-gray-850 my-2" />

                                        <div class="mb-2.5">
                                                <div class=" flex w-full justify-between">
                                                        <div class=" self-center text-xs font-medium">
                                                                {$i18n.t('Enable Prompt Optimization')}
                                                        </div>

                                                        <Switch bind:state={config.ENABLE_PROMPT_OPTIMIZER} />
                                                </div>
                                        </div>

                                        <div class="mb-2.5">
                                                <div class=" flex w-full justify-between">
                                                        <div class=" self-center text-xs font-medium">
                                                                {$i18n.t('Prompt Optimization Model')}
                                                        </div>
                                                        <div class="flex items-center relative">
                                                                <select
                                                                        class="dark:bg-gray-900 w-fit pr-8 rounded-sm px-2 p-1 text-xs bg-transparent outline-hidden text-right"
                                                                        bind:value={config.PROMPT_OPTIMIZER_MODEL}
                                                                        required
                                                                >
                                                                        <option disabled selected value="">{$i18n.t('Select a model')}</option>
                                                                        {#each $models as model}
                                                                                <option value={model.id}>{model.name ?? model.id}</option>
                                                                        {/each}
                                                                </select>
                                                        </div>
                                                </div>
                                        </div>

                                        <div class="mb-2.5 flex flex-col gap-1.5 w-full">
                                                <div class="text-xs font-medium">
                                                        {$i18n.t('Prompt Optimization Prompt Template')}
                                                </div>

                                                <Textarea
                                                        bind:value={config.PROMPT_OPTIMIZER_SYSTEM_PROMPT}
                                                        placeholder={$i18n.t('Write your model template content here')}
                                                />
                                        </div>
                                </div>
                        </div>
                {/if}
        </div>
        <div class="flex justify-end pt-3 text-sm font-medium">
                <button
                        class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
                        type="submit"
                >
                        {$i18n.t('Save')}
                </button>
        </div>
</form>

