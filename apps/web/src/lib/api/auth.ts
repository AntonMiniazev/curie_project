import type { components } from '@curie/api-client';

import { apiFetch } from './client';

export type UserCreateRequest = components['schemas']['UserCreateRequest'];
export type UserLoginRequest = components['schemas']['UserLoginRequest'];
export type TokenResponse = components['schemas']['TokenResponse'];
export type CurrentUserResponse = components['schemas']['CurrentUserResponse'];
export type AvailableRoleResponse = components['schemas']['AvailableRoleResponse'];
export type AvailableRolesResponse = components['schemas']['AvailableRolesResponse'];
export type RefreshTokenRequest = components['schemas']['RefreshTokenRequest'];
export type LogoutRequest = components['schemas']['LogoutRequest'];
export type StreamlitEmbedTokenResponse = components['schemas']['StreamlitEmbedTokenResponse'];

export function getAvailableRoles(): Promise<AvailableRolesResponse> {
	return apiFetch<AvailableRolesResponse>('/api/auth/roles');
}

export function registerUser(request: UserCreateRequest): Promise<TokenResponse> {
	return apiFetch<TokenResponse>('/api/auth/register', {
		method: 'POST',
		body: request
	});
}

export function loginUser(request: UserLoginRequest): Promise<TokenResponse> {
	return apiFetch<TokenResponse>('/api/auth/login', {
		method: 'POST',
		body: request
	});
}

export function getCurrentUser(accessToken?: string): Promise<CurrentUserResponse> {
	return apiFetch<CurrentUserResponse>('/api/auth/me', {
		token: accessToken
	});
}

export function getStreamlitEmbedToken(): Promise<StreamlitEmbedTokenResponse> {
	return apiFetch<StreamlitEmbedTokenResponse>('/api/auth/streamlit-token');
}

export function refreshToken(request?: RefreshTokenRequest): Promise<TokenResponse> {
	return apiFetch<TokenResponse>('/api/auth/refresh', {
		method: 'POST',
		body: request
	});
}

export function logoutUser(request?: LogoutRequest): Promise<null> {
	return apiFetch<null>('/api/auth/logout', {
		method: 'POST',
		body: request
	});
}
