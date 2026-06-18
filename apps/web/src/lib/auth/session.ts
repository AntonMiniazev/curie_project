import { derived, get, writable } from 'svelte/store';

import { getCurrentUser } from '$lib/api/auth';
import type { CurrentUserResponse } from '$lib/api/auth';

export type AuthSessionStatus = 'checking' | 'authenticated' | 'anonymous';

export type AuthSession = {
	status: AuthSessionStatus;
	currentUser: CurrentUserResponse | null;
};

const initialSession: AuthSession = {
	status: 'checking',
	currentUser: null
};

function createSessionStore() {
	const { subscribe, set, update } = writable<AuthSession>(initialSession);

	return {
		subscribe,
		check: async () => {
			if (get({ subscribe }).status === 'authenticated') {
				return;
			}

			update((session) => ({
				...session,
				status: 'checking'
			}));

			try {
				const currentUser = await getCurrentUser();
				set({
					status: 'authenticated',
					currentUser
				});
			} catch {
				set({
					status: 'anonymous',
					currentUser: null
				});
			}
		},
		setCurrentUser: (currentUser: CurrentUserResponse | null) => {
			set({
				status: currentUser ? 'authenticated' : 'anonymous',
				currentUser
			});
		},
		clear: () => {
			set({
				status: 'anonymous',
				currentUser: null
			});
		}
	};
}

export const authSession = createSessionStore();

export const isCheckingAuth = derived(
	authSession,
	($authSession) => $authSession.status === 'checking'
);

export const isAuthenticated = derived(
	authSession,
	($authSession) => $authSession.status === 'authenticated' && Boolean($authSession.currentUser)
);

export const currentUser = derived(authSession, ($authSession) => $authSession.currentUser);
