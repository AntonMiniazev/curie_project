import { env } from '$env/dynamic/public';

type ApiRequestBody = BodyInit | Record<string, unknown> | unknown[] | null | undefined;

type ApiFetch = typeof fetch;

type ApiFetchOptions = Omit<RequestInit, 'body'> & {
	body?: ApiRequestBody;
	fetcher?: ApiFetch;
};

export class ApiError extends Error {
	status: number;
	statusText: string;
	detail: unknown;

	constructor(response: Response, detail: unknown) {
		super(getErrorMessage(response, detail));
		this.name = 'ApiError';
		this.status = response.status;
		this.statusText = response.statusText;
		this.detail = detail;
	}
}

export async function apiFetch<TResponse>(
	path: string,
	options: ApiFetchOptions = {}
): Promise<TResponse> {
	const { fetcher = fetch, headers, body, ...requestInit } = options;
	const requestHeaders = new Headers(headers);

	const requestBody = prepareBody(body, requestHeaders);

	const response = await fetcher(buildApiUrl(path), {
		credentials: 'include',
		...requestInit,
		headers: requestHeaders,
		body: requestBody
	});

	if (!response.ok) {
		throw new ApiError(response, await readResponseBody(response));
	}

	return (await readResponseBody(response)) as TResponse;
}

export function buildApiUrl(path: string): string {
	const cleanBaseUrl = (env.PUBLIC_API_BASE_URL ?? '/api').replace(/\/$/, '');
	const cleanPath = path.startsWith('/') ? path : `/${path}`;

	if (cleanPath.startsWith(`${cleanBaseUrl}/`) || cleanPath === cleanBaseUrl) {
		return cleanPath;
	}

	return `${cleanBaseUrl}${cleanPath}`;
}

function prepareBody(body: ApiRequestBody, headers: Headers): BodyInit | undefined {
	if (body === undefined || body === null) {
		return undefined;
	}

	if (isBodyInit(body)) {
		return body;
	}

	if (!headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}

	return JSON.stringify(body);
}

function isBodyInit(body: ApiRequestBody): body is BodyInit {
	return (
		typeof body === 'string' ||
		body instanceof Blob ||
		body instanceof FormData ||
		body instanceof URLSearchParams ||
		body instanceof ArrayBuffer ||
		ArrayBuffer.isView(body)
	);
}

async function readResponseBody(response: Response): Promise<unknown> {
	if (response.status === 204) {
		return null;
	}

	const contentType = response.headers.get('Content-Type') ?? '';

	if (contentType.includes('application/json')) {
		return response.json();
	}

	return response.text();
}

function getErrorMessage(response: Response, detail: unknown): string {
	if (isErrorDetail(detail)) {
		return detail.detail;
	}

	if (typeof detail === 'string' && detail.length > 0) {
		return detail;
	}

	return `API request failed with ${response.status} ${response.statusText}`;
}

function isErrorDetail(value: unknown): value is { detail: string } {
	return (
		typeof value === 'object' &&
		value !== null &&
		'detail' in value &&
		typeof value.detail === 'string'
	);
}
