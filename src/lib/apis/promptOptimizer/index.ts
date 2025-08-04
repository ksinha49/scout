import { WEBUI_API_BASE_URL } from '$lib/constants';

export const optimizePrompt = async (token: string, prompt: string) => {
        let error = null;

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
        })
                .then(async (res) => {
                        if (!res.ok) throw await res.json();
                        return res.json();
                })
                .catch((err) => {
                        console.log(err);
                        if ('detail' in err) {
                                error = err.detail;
                        } else {
                                error = err;
                        }
                        return null;
                });

        if (error) {
                throw error;
        }

        return res?.optimized;
};

