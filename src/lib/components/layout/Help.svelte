<script lang="ts">
	import { onMount, tick, getContext } from 'svelte';

	const i18n = getContext('i18n');

        import ShortcutsModal from '../chat/ShortcutsModal.svelte';
        import Tooltip from '../common/Tooltip.svelte';
        import HelpMenu from './Help/HelpMenu.svelte';
        import ShieldCheck from '$lib/components/icons/ShieldCheck.svelte';
        import { showSecuritymd } from '$lib/stores';

	let showShortcuts = false;
</script>

<div class=" hidden lg:flex fixed bottom-0 right-0 px-1 py-1 z-20 gap-1">
        <button
                id="show-shortcuts-button"
                class="hidden"
                on:click={() => {
                        showShortcuts = !showShortcuts;
                }}
        />

        <Tooltip content={$i18n.t('Security')} placement="left">
                <button
                        class="text-gray-600 dark:text-gray-300 bg-gray-300/20 size-4 flex items-center justify-center rounded-full"
                        on:click={() => {
                                showSecuritymd.set(true);
                        }}
                >
                        <ShieldCheck className="size-3" />
                </button>
        </Tooltip>

        <HelpMenu
                showDocsHandler={() => {
                        showShortcuts = !showShortcuts;
                }}
                showShortcutsHandler={() => {
                        showShortcuts = !showShortcuts;
                }}
        >
                <Tooltip content={$i18n.t('Help')} placement="left">
                        <button
                                class="text-gray-600 dark:text-gray-300 bg-gray-300/20 size-4 flex items-center justify-center text-[0.7rem] rounded-full"
                        >
                                ?
                        </button>
                </Tooltip>
        </HelpMenu>
</div>

<ShortcutsModal bind:show={showShortcuts} />
