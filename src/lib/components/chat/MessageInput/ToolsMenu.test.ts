import { render, fireEvent } from '@testing-library/svelte';
import { setContext, tick } from 'svelte';
import ToolsMenu from './ToolsMenu.svelte';
import { config, user, tools as toolsStore } from '$lib/stores';

describe('ToolsMenu', () => {
    beforeEach(() => {
        setContext('i18n', { t: (s: string) => s });
        config.set({
            features: {
                enable_web_search: true,
                enable_code_interpreter: true,
                enable_image_generation: true
            }
        } as any);
        user.set({ role: 'admin', permissions: { features: { web_search: true, code_interpreter: true, image_generation: true } } } as any);
        toolsStore.set([{ id: 'test-tool', name: 'Test Tool', meta: { description: 'desc' } }]);
    });

    test('toggles selections via item click', async () => {
        const { getByText, component } = render(ToolsMenu, {
            props: {
                selectedToolIds: [],
                webSearchEnabled: false,
                codeInterpreterEnabled: false,
                imageGenerationEnabled: false,
                onClose: () => {}
            },
            slots: { default: '<button>open</button>' }
        });

        await fireEvent.click(getByText('open'));
        await tick();
        await fireEvent.click(getByText('Web Search'));
        expect(component.$$.ctx[component.$$.props['webSearchEnabled']]).toBe(true);

        await fireEvent.click(getByText('Test Tool'));
        const selectedToolIds = component.$$.ctx[component.$$.props['selectedToolIds']];
        expect(selectedToolIds).toContain('test-tool');
    });
});
