<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';

	import { ApiError } from '$lib/api/client';
	import { logoutUser } from '$lib/api/auth';
	import { getReports, type ReportItem } from '$lib/api/reports';
	import { authSession, isAuthenticated, isCheckingAuth } from '$lib/auth/session';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import LoadingLine from '$lib/components/LoadingLine.svelte';
	import { mainNavigationItems } from '$lib/navigation';

	let reports = $state<ReportItem[]>([]);
	let isLoadingReports = $state(false);
	let errorMessage = $state<string | null>(null);
	let isProfileOpen = $state(false);

	onMount(() => {
		void initializePage();
	});

	async function initializePage() {
		await authSession.check();

		if (get(isAuthenticated)) {
			await loadReports();
		}
	}

	async function loadReports() {
		errorMessage = null;
		isLoadingReports = true;

		try {
			const response = await getReports();
			reports = response.items;
		} catch (error) {
			errorMessage = getErrorMessage(
				error,
				'Could not load reports. Check that the API is running.'
			);
		} finally {
			isLoadingReports = false;
		}
	}

	async function handleLogout() {
		try {
			await logoutUser();
		} catch {
			// Local logout should still clear the browser session if the API request fails.
		}

		authSession.clear();
		reports = [];
		isProfileOpen = false;
	}

	function primaryRoleShortDescription() {
		const user = $authSession.currentUser;
		return user?.role_short_descriptions[0] ?? 'Reporting access';
	}

	function primaryRoleDescription() {
		const user = $authSession.currentUser;
		return user?.role_descriptions[0] ?? primaryRoleShortDescription();
	}

	function displayName() {
		const user = $authSession.currentUser;
		return user?.display_name || user?.email || 'Curie user';
	}

	function createdAtLabel() {
		const createdAt = $authSession.currentUser?.created_at;

		if (!createdAt) {
			return 'Account date unavailable';
		}

		return new Intl.DateTimeFormat('en', {
			year: 'numeric',
			month: 'short',
			day: '2-digit'
		}).format(new Date(createdAt));
	}

	function getErrorMessage(error: unknown, fallback: string): string {
		if (error instanceof ApiError) {
			return error.message;
		}

		return fallback;
	}
</script>

<svelte:head>
	<title>Curie Reports</title>
</svelte:head>

<svelte:body class:overflow-hidden={isProfileOpen} />

<AppHeader pageName="Curie reports" navigationItems={mainNavigationItems} selectedHref="/curie" />

<main class="curie-page min-h-screen px-6 py-8">
	{#if $isCheckingAuth}
		<section class="mx-auto max-w-6xl">
			<LoadingLine />
		</section>
	{:else if $isAuthenticated}
		<section class="mx-auto max-w-6xl">
			<header
				class="mb-8 flex flex-col gap-5 border-b border-[var(--curie-border)] pb-6 md:flex-row md:items-end md:justify-between"
			>
				<div>
					<h1 class="text-3xl font-semibold text-[var(--curie-text)]">Reporting workspace</h1>
					<p class="mt-2 max-w-2x2 text-[var(--curie-text-muted)]">
						Select a report to open its workspace. Streamlit embeds will be attached to these report
						pages later.
					</p>
				</div>

				{#if $authSession.currentUser}
					<button
						class="curie-card curie-card--clickable min-w-[14rem] p-4"
						type="button"
						aria-haspopup="dialog"
						aria-expanded={isProfileOpen}
						onclick={() => (isProfileOpen = true)}
					>
						<p class="font-semibold text-[var(--curie-text)]">{displayName()}</p>
						<p class="mt-1 text-sm text-[var(--curie-text-muted)]">
							{primaryRoleShortDescription()}
						</p>
					</button>
				{/if}
			</header>

			{#if errorMessage}
				<p class="curie-alert curie-alert--danger mb-5 px-4 py-3 text-sm">{errorMessage}</p>
			{/if}

			{#if isLoadingReports}
				<p class="text-[var(--curie-text-muted)]">Loading reports...</p>
			{:else if reports.length === 0}
				<section class="curie-card curie-card--flat border-dashed p-6">
					<h2 class="text-lg font-semibold text-[var(--curie-text)]">No reports available</h2>
					<p class="mt-2 text-[var(--curie-text-muted)]">
						The API returned an empty report list. Seed or enable reports in PostgreSQL to show them
						here.
					</p>
				</section>
			{:else}
				<section class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
					{#each reports as report (report.id)}
						<a
							class="curie-card curie-card--clickable p-5"
							href={resolve(`/curie/reports/${report.id}`)}
						>
							<div class="mb-4 flex items-start justify-between gap-3">
								<div>
									<p class="curie-eyebrow text-xs">{report.category}</p>
									<h2 class="mt-1 text-lg font-semibold text-[var(--curie-red-test)]">
										{report.title}
									</h2>
								</div>
							</div>
							<p class="text-sm leading-6 text-[var(--curie-text-muted)]">
								{report.description || 'Report workspace template is ready for a Streamlit app.'}
							</p>
						</a>
					{/each}
				</section>
			{/if}
		</section>
	{:else if !$isCheckingAuth}
		<section
			class="mx-auto grid min-h-[calc(100vh-4rem)] max-w-5xl gap-8 lg:grid-cols-[1fr_380px] lg:items-center"
		>
			<div>
				<h1 class="mb-4 text-4xl font-semibold text-[var(--curie-text)]">Reports require login</h1>
				<p class="text-lg leading-8 text-[var(--curie-text-muted)]">
					Create an account or sign in to access the reporting workspace.
				</p>
			</div>

			<nav class="curie-card curie-card--flat p-6">
				<a
					class="curie-button curie-button--primary mb-4 block px-4 py-2 text-center"
					href={resolve('/curie/login')}
				>
					Sign in
				</a>
				<a class="curie-button block px-4 py-2 text-center" href={resolve('/curie/register')}>
					Create account
				</a>
			</nav>
		</section>
	{/if}
</main>

{#if isProfileOpen && $authSession.currentUser}
	<div
		class="curie-overlay fixed inset-0 z-50 grid place-items-center bg-[var(--curie-overlay-bg)] px-4"
		role="presentation"
	>
		<button
			class="absolute inset-0 cursor-default"
			type="button"
			aria-label="Close user details"
			onclick={() => (isProfileOpen = false)}
		></button>
		<div
			class="curie-card curie-card--surface relative z-10 w-full max-w-[42rem] p-6"
			role="dialog"
			aria-modal="true"
			aria-labelledby="curie-profile-title"
		>
			<h2 id="curie-profile-title" class="text-2xl font-semibold text-[var(--curie-text)]">
				User: {displayName()}
			</h2>
			<p class="mt-2 text-base font-medium text-[var(--curie-text-muted)]">
				Email: {$authSession.currentUser.email}
			</p>

			<p class="mt-4 whitespace-nowrap text-sm text-[var(--curie-text)]">
				<span class="font-semibold">Access:</span>
				{primaryRoleDescription()}
			</p>
			<p class="mt-4 text-sm text-[var(--curie-text-muted)]">
				<span class="font-semibold">Registration date:</span>
				{createdAtLabel()}
			</p>

			<div class="mt-6 flex justify-end gap-3">
				<button class="curie-button px-4 py-2 text-sm" type="button" onclick={handleLogout}>
					Logout
				</button>
			</div>
		</div>
	</div>
{/if}
