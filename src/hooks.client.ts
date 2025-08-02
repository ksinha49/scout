import type { HandleFetch } from '@sveltejs/kit';
import { handleSessionExpired } from '$lib/utils/auth';


export const handleFetch: HandleFetch = async ({ request, fetch }) => {
    const response = await fetch(request);
    if (response.status === 401 && localStorage.getItem('token')) {
        handleSessionExpired();
    }
    return response;
};
