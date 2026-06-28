<script lang="ts">
	import { page } from '$app/state';
	import { env } from '$env/dynamic/public';
	import { resolve } from '$app/paths';
	import { Maximize2, Minimize2 } from '@lucide/svelte';
	import { onMount } from 'svelte';

	import { ApiError } from '$lib/api/client';
	import { getReports, type ReportItem } from '$lib/api/reports';
	import { authSession, isAuthenticated, isCheckingAuth } from '$lib/auth/session';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import LoadingLine from '$lib/components/LoadingLine.svelte';
	import { mainNavigationItems } from '$lib/navigation';

	let report = $state<ReportItem | null>(null);
	let errorMessage = $state<string | null>(null);
	let isLoading = $state(false);
	let isFrameExpanded = $state(false);
	let curieTheme = $state<'day' | 'night'>('day');
	let isAuthReady = $state(false);
	let reportRequestId = 0;

	const reportId = $derived(page.params.reportId);
	const streamlitBaseUrl = $derived(
		(env.PUBLIC_STREAMLIT_BASE_URL ?? '/streamlit').replace(/\/$/, '')
	);
	const streamlitUrl = $derived(
		report ? appendReportTheme(`${streamlitBaseUrl}${report.streamlit_path}`) : null
	);

	onMount(() => {
		syncTheme();
		const themeObserver = new MutationObserver(syncTheme);
		themeObserver.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['data-theme']
		});
		void initializePage();

		return () => {
			themeObserver.disconnect();
		};
	});

	$effect(() => {
		const nextReportId = reportId;

		if (!nextReportId || !isAuthReady || !$isAuthenticated) {
			return;
		}

		void loadReport(nextReportId);
	});

	async function initializePage() {
		await authSession.check({ force: true });
		isAuthReady = true;
	}

	async function loadReport(nextReportId: string) {
		const currentRequestId = ++reportRequestId;

		errorMessage = null;
		report = null;
		isLoading = true;

		try {
			const response = await getReports();
			const nextReport = response.items.find((item) => item.id === nextReportId) ?? null;

			if (currentRequestId !== reportRequestId) {
				return;
			}

			report = nextReport;

			if (!report) {
				errorMessage = 'Report was not found in the API response.';
			}
		} catch (error) {
			if (currentRequestId !== reportRequestId) {
				return;
			}

			errorMessage = getErrorMessage(error);
		} finally {
			if (currentRequestId === reportRequestId) {
				isLoading = false;
			}
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

	function syncTheme() {
		curieTheme = document.documentElement.dataset.theme === 'night' ? 'night' : 'day';
	}

	function appendReportTheme(url: string): string {
		const separator = url.includes('?') ? '&' : '?';
		return `${url}${separator}curie_theme=${encodeURIComponent(curieTheme)}`;
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
				<div class="mt-2 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
					<p class="max-w-3xl text-[var(--curie-text-muted)]">
						{report.description || 'Report workspace template is ready for a Streamlit app.'}
					</p>
					{#if streamlitUrl && !isFrameExpanded}
						<button
							class="curie-report-inline-button"
							type="button"
							aria-label="Expand report frame"
							aria-pressed={isFrameExpanded}
							onclick={toggleFrameExpanded}
						>
							<Maximize2 class="h-4 w-4" aria-hidden="true" />
							<span>Expand</span>
						</button>
					{/if}
				</div>
			</header>

			<section
				class="curie-card curie-static-card curie-report-shell"
				class:curie-report-expanded={isFrameExpanded}
			>
				{#if streamlitUrl}
					{#if isFrameExpanded}
						<button
							class="curie-report-collapse-button"
							type="button"
							aria-label="Collapse report frame"
							aria-pressed={isFrameExpanded}
							onclick={toggleFrameExpanded}
						>
							<Minimize2 class="h-4 w-4" aria-hidden="false" />
						</button>
					{/if}
					{#key report.id}
						<iframe class="curie-report-frame" title={report.title} src={streamlitUrl}></iframe>
					{/key}
				{:else}
					<div class="grid min-h-[560px] place-items-center p-6">
						<p class="text-[var(--curie-text-muted)]">Report workspace URL is not configured.</p>
					</div>
				{/if}
			</section>
		{/if}
	</section>
</main>
