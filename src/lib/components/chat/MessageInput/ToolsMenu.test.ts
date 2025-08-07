/** @vitest-environment jsdom */
import { render, fireEvent } from '@testing-library/svelte';
import { tick } from 'svelte';
import { describe, test, expect, beforeEach } from 'vitest';
import ToolsMenu from './ToolsMenuTestWrapper.svelte';
import { config, user, tools as toolsStore } from '$lib/stores';

describe('ToolsMenu', () => {
	beforeEach(() => {
		config.set({
			features: {
				enable_web_search: true,
				enable_code_interpreter: true,
				enable_image_generation: true
			}
		} as any);
		user.set({
			role: 'admin',
			permissions: {
				features: { web_search: true, code_interpreter: true, image_generation: true }
			}
		} as any);
		toolsStore.set([{ id: 'test-tool', name: 'Test Tool', meta: { description: 'desc' } }]);
	});

	test('toggles selections via item click', async () => {
		const { getByText, component } = render(ToolsMenu, {
			props: {
				selectedToolIds: [],
				webSearchEnabled: false,
				codeInterpreterEnabled: false,
				imageGenerationEnabled: false,
				extendedThinkingEnabled: false,
				reasoningCapable: true,
				onClose: () => {}
			},
			context: new Map([
				[
					'i18n',
					{
						subscribe: (run: Function) => {
							run({ t: (s: string) => s });
							return () => {};
						}
					}
				]
			])
		});

		await fireEvent.click(getByText('open'));
		await tick();
		await fireEvent.click(getByText('Extended Thinking'));
		expect(component.$$.ctx[component.$$.props['extendedThinkingEnabled']]).toBe(true);

		// Reopen menu in case it closed after the previous selection
		await fireEvent.click(getByText('open'));
		await tick();
		await fireEvent.click(getByText('Web Search'));
		expect(component.$$.ctx[component.$$.props['webSearchEnabled']]).toBe(true);

		// Reopen menu again for tool selection
		await fireEvent.click(getByText('open'));
		await tick();
		await fireEvent.click(getByText('Tools'));
		await tick();
		await fireEvent.click(getByText('Test Tool'));
		const selectedToolIds = component.$$.ctx[component.$$.props['selectedToolIds']];
		expect(selectedToolIds).toContain('test-tool');
	});
});

test('extended thinking sets temperature to 1 and restores previous value', async () => {
	const { component } = render(ToolsMenu, {
		props: {
			selectedToolIds: [],
			webSearchEnabled: false,
			codeInterpreterEnabled: false,
			imageGenerationEnabled: false,
			extendedThinkingEnabled: false,
			reasoningCapable: true,
			onClose: () => {},
			params: { temperature: 0.7 }
		},
		context: new Map([
			[
				'i18n',
				{
					subscribe: (run: Function) => {
						run({ t: (s: string) => s });
						return () => {};
					}
				}
			]
		])
	});

	const getParams = () => component.$$.ctx[component.$$.props['params']];
	expect(getParams().temperature).toBe(0.7);

	component.$set({ extendedThinkingEnabled: true });
	await tick();
	expect(getParams().temperature).toBe(1);

	component.$set({ extendedThinkingEnabled: false });
	await tick();
	expect(getParams().temperature).toBe(0.7);
});
