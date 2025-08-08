/** @vitest-environment jsdom */
import { render } from '@testing-library/svelte';
import { tick } from 'svelte';
import Collapsible from '$lib/components/common/Collapsible.svelte';

describe('Reasoning UI', () => {
        test('transitions from Thinking... to Thought for X seconds', async () => {
                const { getByText, component } = render(Collapsible, {
                        props: {
                                attributes: { type: 'reasoning', done: 'false' }
                        },
                        context: new Map([
                                [
                                        'i18n',
                                        {
                                                subscribe: (run: Function) => {
                                                        run({
                                                                t: (s: string, vars?: Record<string, any>) =>
                                                                        vars
                                                                                ? s.replace(/\{\{(.*?)\}\}/g, (_, k) =>
                                                                                          vars[k.trim()] ?? ''
                                                                                  )
                                                                                : s,
                                                                languages: ['en-US']
                                                        });
                                                        return () => {};
                                                }
                                        }
                                ]
                        ])
                });

                getByText('Thinking...');

                component.$set({ attributes: { type: 'reasoning', done: 'true', duration: 3 } });
                await tick();

                getByText('Thought for 3 seconds');
        });
});
