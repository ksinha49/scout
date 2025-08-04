import { WEBUI_API_BASE_URL } from '$lib/constants';

export const optimizePrompt = async (token: string, prompt: string) => {
        try {
                const res = await fetch(`${WEBUI_API_BASE_URL}/prompt-optimizer/optimize`, {
                        method: 'POST',
                        headers: {
                                Accept: 'application/json',
                                'Content-Type': 'application/json',
                                authorization: `Bearer ${token}`
                        },
                        body: JSON.stringify({
                                prompt: prompt
                        })
                });

                if (!res.ok) {
                        throw await res.json();
                }

                const data = await res.json();
                return data?.optimized;
        } catch (err: any) {
                console.log(err);
                const error = err?.detail ?? 'Prompt optimization failed';
                throw error;
        }
};

