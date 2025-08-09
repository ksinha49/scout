<script lang="ts">
        import { onMount, getContext, createEventDispatcher } from 'svelte';

        import { WEBUI_NAME } from '$lib/stores';

        import { WEBUI_VERSION } from '$lib/constants';
        import { getSecuritymd } from '$lib/apis';

	import Modal from './common/Modal.svelte';

        const i18n = getContext('i18n');

        export let show = false;

        let securitymd = null;
        const dispatch = createEventDispatcher();

        function markShown() {
                dispatch('dismiss');
        }

        onMount(async () => {
                const res = await getSecuritymd();
                securitymd = res;
        });
</script>

<Modal bind:show>
	<div class="px-5 pt-4 dark:text-gray-300 text-gray-700">
		<div class="flex justify-between items-start">
			<div class="text-xl font-semibold">
				{$i18n.t('Ameritas AI Application Security Policy')}				
			</div>
                        <button
                                class="self-center"
                                on:click={() => {
                                        markShown();
                                        show = false;
                                }}
                        >
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
		<div class="flex items-center mt-1">
			<div class="text-sm dark:text-gray-200">{$WEBUI_NAME}</div>
			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-200 dark:bg-gray-700" />
			<div class="text-sm dark:text-gray-200">
				v{WEBUI_VERSION}
			</div>
		</div>
	</div>

	<div class=" w-full p-4 px-5 text-gray-700 dark:text-gray-100">
		<div class=" overflow-y-scroll max-h-80 scrollbar-hidden">
			<div class="mb-3">
				{#if securitymd}
                                    {#each Object.keys(securitymd) as section}
                                      <section>
                                         <h3 style="font-size: 1.25rem;margin-bottom: 0.5rem;">{section}</h3>
                                         <ul style="margin-left: 1.5rem;">
                                           {#each securitymd[section] as item}
                                             <li style="margin-bottom: 0.5rem;">
                                               {@html item.raw}
                                             </li>
                                           {/each}
                                        </ul>
                                      </section>
                                    {/each}						
				{/if}
			</div>
		</div>
		<div class="flex justify-end pt-3 text-sm font-medium">
                        <button
                                on:click={() => {
                                        markShown();
                                        show = false;
                                }}
                                class=" px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg"
                        >
				<span class="relative">{$i18n.t("Continue")}</span>
			</button>
		</div>
	</div>
</Modal>
