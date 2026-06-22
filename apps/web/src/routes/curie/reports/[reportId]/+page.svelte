<script lang="ts">
	import { page } from '$app/state';
	import { env } from '$env/dynamic/public';
	import { resolve } from '$app/paths';
	import { Maximize2, Minimize2 } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';

	import { ApiError } from '$lib/api/client';
	import { getStreamlitEmbedToken } from '$lib/api/auth';
	import { getReports, type ReportItem } from '$lib/api/reports';
	import { authSession, isAuthenticated, isCheckingAuth } from '$lib/auth/session';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import LoadingLine from '$lib/components/LoadingLine.svelte';
	import { mainNavigationItems } from '$lib/navigation';

	let report = $state<ReportItem | null>(null);
	let streamlitToken = $state<string | null>(null);
	let errorMessage = $state<string | null>(null);
	let isLoading = $state(false);
	let isFrameExpanded = $state(false);

	const reportId = $derived(page.params.reportId);
	const streamlitBaseUrl = $derived(
		(env.PUBLIC_STREAMLIT_BASE_URL ?? '/streamlit').replace(/\/$/, '')
	);
	const streamlitUrl = $derived(
		report && streamlitToken
			? withStreamlitToken(`${streamlitBaseUrl}${report.streamlit_path}`, streamlitToken)
			: null
	);

	onMount(() => {
		void initializePage();
	});

	async function initializePage() {
		await authSession.check({ force: true });

		if (get(isAuthenticated)) {
			await loadReport();
		}
	}

	async function loadReport() {
		errorMessage = null;
		isLoading = true;

		try {
			const [response, tokenResponse] = await Promise.all([
				getReports(),
				getStreamlitEmbedToken()
			]);
			report = response.items.find((item) => item.id === reportId) ?? null;
			streamlitToken = tokenResponse.embed_token;

			if (!report) {
				errorMessage = 'Report was not found in the API response.';
			}
		} catch (error) {
			errorMessage = getErrorMessage(error);
		} finally {
			isLoading = false;
		}
	}

	function getErrorMessage(error: unknown): string {
		if (error instanceof ApiError) {
			return error.message;
		}

		return 'Could not load report metadata. Check that the API is running.';
	}

	function toggleFrameExpanded() {
		isFrameExpanded = !isFrameExpanded;
	}

	function withStreamlitToken(url: string, token: string): string {
		const separator = url.includes('?') ? '&' : '?';
		return `${url}${separator}curie_token=${encodeURIComponent(token)}`;
	}
</script>

<svelte:head>
	<title>{report?.title ?? 'Report'} | Curie</title>
</svelte:head>

<AppHeader pageName="Curie report" navigationItems={mainNavigationItems} selectedHref="/curie" />

<main class="min-h-screen px-6 py-8">
	<section class="mx-auto max-w-6xl">
		<a
			class="mb-6 inline-block text-sm font-medium text-[var(--curie-blue-l1)] hover:underline"
			href={resolve('/curie')}
		>
			Back to reports
		</a>

		{#if $isCheckingAuth}
			<LoadingLine />
		{:else if !$isAuthenticated}
			<section class="curie-card-flat p-6">
				<h1 class="text-2xl font-semibold text-[var(--curie-text)]">Login required</h1>
				<p class="mt-2 text-[var(--curie-text-muted)]">Sign in before opening report workspaces.</p>
				<a class="curie-button-primary mt-5 inline-block px-4 py-2" href={resolve('/curie/login')}>
					Sign in
				</a>
			</section>
		{:else if isLoading}
			<p class="text-[var(--curie-text-muted)]">Loading report...</p>
		{:else if errorMessage}
			<section class="curie-card-flat p-6">
				<h1 class="text-2xl font-semibold text-[var(--curie-text)]">Report unavailable</h1>
				<p class="mt-2 text-[var(--curie-red-l1)]">{errorMessage}</p>
			</section>
		{:else if report}
			<header class="mb-6 border-b border-[var(--curie-border)] pb-6">
				<p class="curie-eyebrow mb-2">{report.category}</p>
				<h1 class="text-3xl font-semibold text-[var(--curie-text)]">{report.title}</h1>
				<p class="mt-2 max-w-3xl text-[var(--curie-text-muted)]">
					{report.description || 'Report workspace template is ready for a Streamlit app.'}
				</p>
			</header>

			<section class="curie-card curie-report-shell" class:curie-report-expanded={isFrameExpanded}>
				{#if streamlitUrl}
					<button
						class="curie-report-expand-button"
						type="button"
						aria-label={isFrameExpanded ? 'Collapse report frame' : 'Expand report frame'}
						aria-pressed={isFrameExpanded}
						onclick={toggleFrameExpanded}
					>
						{#if isFrameExpanded}
							<Minimize2 class="h-4 w-4" aria-hidden="true" />
						{:else}
							<Maximize2 class="h-4 w-4" aria-hidden="true" />
						{/if}
					</button>
					<iframe
						class="curie-report-frame"
						title={report.title}
						src={streamlitUrl}
						loading="lazy"
					></iframe>
				{:else}
					<div class="grid min-h-[560px] place-items-center p-6">
						<p class="text-[var(--curie-text-muted)]">Report workspace URL is not configured.</p>
					</div>
				{/if}
			</section>
		{/if}
	</section>
</main>

<style>
	.curie-report-shell {
		position: relative;
		overflow: hidden;
	}

	.curie-report-shell :global(.curie-report-frame) {
		border-radius: var(--curie-radius-xm);
	}

	.curie-report-expand-button {
		position: absolute;
		right: 1rem;
		top: 1rem;
		z-index: 2;
		display: inline-flex;
		height: 2.25rem;
		width: 2.25rem;
		align-items: center;
		justify-content: center;
		border: 1px solid var(--curie-border);
		border-radius: 0.5rem;
		background: color-mix(in srgb, var(--curie-surface) 92%, transparent);
		color: var(--curie-text);
		box-shadow: 0 8px 24px rgba(29, 53, 87, 0.16);
		transition:
			background-color 0.15s ease,
			color 0.15s ease,
			border-color 0.15s ease;
	}

	.curie-report-expand-button:hover {
		border-color: var(--curie-blue-l2);
		color: var(--curie-blue-l3);
	}
</style>
