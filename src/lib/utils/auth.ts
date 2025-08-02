import { goto } from '$app/navigation';
import { toast } from 'svelte-sonner';

let logoutTimer: number | null = null;

export function handleSessionExpired() {
    localStorage.removeItem('token');
    toast.error('Your session has expired. Please log in again.');
    const redirect = encodeURIComponent(
        window.location.pathname + window.location.search
    );
    goto(`/auth?redirect=${redirect}`);
}

export function scheduleTokenExpiration(expiresAt?: number) {
    if (!expiresAt) return;
    const timeout = expiresAt * 1000 - Date.now();
    if (timeout <= 0) {
        handleSessionExpired();
    } else {
        if (logoutTimer) {
            clearTimeout(logoutTimer);
        }
        logoutTimer = window.setTimeout(() => {
            handleSessionExpired();
        }, timeout);
    }
}
