<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { ApiError } from '$lib/api/client';
	import { getCurrentUser, loginUser } from '$lib/api/auth';
	import { authSession } from '$lib/auth/session';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import TextField from '$lib/components/TextField.svelte';
	import { mainNavigationItems } from '$lib/navigation';

	let email = $state('');
	let password = $state('');
	let errorMessage = $state<string | null>(null);
	let isSubmitting = $state(false);
	let registeredMessage = $derived(
		page.url.searchParams.get('registered') === 'true'
			? 'Account created. Sign in with your new password to continue.'
			: null
	);

	$effect(() => {
		const emailParam = page.url.searchParams.get('email');

		if (emailParam && !email) {
			email = emailParam;
		}
	});

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = null;
		isSubmitting = true;

		try {
			const tokenResponse = await loginUser({ email, password });
			const currentUser = await getCurrentUser(tokenResponse.access_token);
			authSession.setCurrentUser(currentUser);

			await goto(resolve('/curie'));
		} catch (error) {
			errorMessage = getErrorMessage(error);
		} finally {
			isSubmitting = false;
		}
	}

	function getErrorMessage(error: unknown): string {
		if (error instanceof ApiError) {
			return error.message;
		}

		return 'Login failed. Check your connection and try again.';
	}
</script>

<svelte:head>
	<title>Login | Curie</title>
</svelte:head>

<AppHeader pageName="Curie login" navigationItems={mainNavigationItems} selectedHref="/curie" />

<main class="min-h-screen px-6 py-10">
	<section class="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1fr_420px] lg:items-center">
		<div class="max-w-2xl">
			<a class="curie-eyebrow mb-3 inline-block" href={resolve('/curie')}> Curie </a>
			<h1 class="mb-4 text-4xl font-semibold text-[var(--curie-text)]">Sign in to reports</h1>
			<p class="text-lg leading-8 text-[var(--curie-text-muted)]">
				Use your Curie account to access the reporting workspace. New users can create an account
				and select the role that defines their data context.
			</p>
		</div>

		<form class="curie-card-flat p-6" onsubmit={handleSubmit}>
			<div class="mb-6">
				<h2 class="text-xl font-semibold text-[var(--curie-text)]">Login</h2>
				<p class="mt-2 text-sm text-[var(--curie-text-muted)]">
					Enter the email and password used during registration.
				</p>
			</div>

			<TextField label="Email" type="email" autocomplete="email" required bind:value={email} />
			<TextField
				label="Password"
				type="password"
				autocomplete="current-password"
				required
				bind:value={password}
			/>

			{#if registeredMessage}
				<p
					class="mb-4 rounded-[var(--curie-radius-xm)] border border-[var(--curie-border)] bg-[var(--curie-control-bg)] px-3 py-2 text-sm text-[var(--curie-text)]"
				>
					{registeredMessage}
				</p>
			{/if}

			{#if errorMessage}
				<p class="curie-alert-danger mb-4 px-3 py-2 text-sm">{errorMessage}</p>
			{/if}

			<button
				class="curie-button-primary w-full px-4 py-2 disabled:cursor-not-allowed disabled:opacity-60"
				type="submit"
				disabled={isSubmitting}
			>
				{isSubmitting ? 'Signing in...' : 'Sign in'}
			</button>

			<p class="mt-5 text-center text-sm text-[var(--curie-text-muted)]">
				Need an account?
				<a
					class="font-medium text-[var(--curie-blue-l3)] hover:underline"
					href={resolve('/curie/register')}
				>
					Create one
				</a>
			</p>
		</form>
	</section>
</main>
