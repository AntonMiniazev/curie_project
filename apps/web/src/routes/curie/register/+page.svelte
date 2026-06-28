<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';

	import {
		getAvailableRoles,
		getCurrentUser,
		registerUser,
		type AvailableRoleResponse
	} from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';
	import { authSession } from '$lib/auth/session';

	import AppHeader from '$lib/components/AppHeader.svelte';
	import TextField from '$lib/components/TextField.svelte';
	import { mainNavigationItems } from '$lib/navigation';

	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let selectedRole = $state('');
	let roles = $state<AvailableRoleResponse[]>([]);
	let errorMessage = $state<string | null>(null);
	let isLoadingRoles = $state(true);
	let isSubmitting = $state(false);

	onMount(() => {
		void loadRoles();
	});

	async function loadRoles() {
		errorMessage = null;
		isLoadingRoles = true;

		try {
			const response = await getAvailableRoles();
			roles = response.items;
			selectedRole = response.items[0]?.name ?? '';
		} catch (error) {
			errorMessage = getErrorMessage(error, 'Could not load roles. Check that the API is running.');
		} finally {
			isLoadingRoles = false;
		}
	}

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = null;
		isSubmitting = true;

		try {
			const tokenResponse = await registerUser({
				email,
				password,
				display_name: displayName || null,
				role: selectedRole
			});
			try {
				const currentUser = await getCurrentUser(tokenResponse.access_token);
				authSession.setCurrentUser(currentUser);
				await goto(resolve('/curie'));
			} catch {
				await goto(resolve(`/curie/login?email=${encodeURIComponent(email)}&registered=true`));
			}
		} catch (error) {
			errorMessage = getErrorMessage(
				error,
				'Registration failed. Check your inputs and try again.'
			);
		} finally {
			isSubmitting = false;
		}
	}

	function getErrorMessage(error: unknown, fallback: string): string {
		if (error instanceof ApiError) {
			return error.message;
		}

		return fallback;
	}
</script>

<svelte:head>
	<title>Register | Curie</title>
</svelte:head>

<AppHeader pageName="Curie register" navigationItems={mainNavigationItems} selectedHref="/curie" />

<main class="min-h-screen px-6 py-10">
	<section class="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1fr_460px] lg:items-center">
		<div class="max-w-2xl">
			<p class="curie-eyebrow mb-3">Curie</p>
			<h1 class="mb-4 text-4xl font-semibold text-[var(--curie-text)]">Create your account</h1>
			<p class="text-lg leading-8 text-[var(--curie-text-muted)]">
				Choose the role that matches the data context you want to explore.
			</p>
		</div>

		<form class="curie-card curie-card--flat p-6" onsubmit={handleSubmit}>
			<div class="mb-6">
				<h2 class="text-xl font-semibold text-[var(--curie-text)]">Register</h2>
				<p class="mt-2 text-sm text-[var(--curie-text-muted)]">
					All fields except display name are required.
				</p>
			</div>

			<TextField label="Email" type="email" autocomplete="email" required bind:value={email} />
			<TextField label="Display name" autocomplete="name" bind:value={displayName} />
			<TextField
				label="Password"
				type="password"
				autocomplete="new-password"
				minlength={5}
				required
				bind:value={password}
			/>

			<label class="mb-4 block">
				<span class="mb-2 block text-sm font-medium text-[var(--curie-text)]">Role</span>
				<select
					class="curie-input disabled:opacity-60"
					bind:value={selectedRole}
					disabled={isLoadingRoles || roles.length === 0}
					required
				>
					{#if isLoadingRoles}
						<option class="curie-select__option" value="">Loading roles...</option>
					{:else}
						{#each roles as role (role.name)}
							<option class="curie-select__option" value={role.name}>{role.label}</option>
						{/each}
					{/if}
				</select>
			</label>

			{#if selectedRole}
				<p class="mb-4 text-sm text-[var(--curie-text-muted)]">
					{roles.find((role) => role.name === selectedRole)?.description}
				</p>
			{/if}

			{#if errorMessage}
				<p class="curie-alert curie-alert--danger mb-4 px-3 py-2 text-sm">{errorMessage}</p>
			{/if}

			<button
				class="curie-button curie-button--primary w-full px-4 py-2 disabled:cursor-not-allowed disabled:opacity-60"
				type="submit"
				disabled={isSubmitting || isLoadingRoles || !selectedRole}
			>
				{isSubmitting ? 'Creating account...' : 'Create account'}
			</button>

			<p class="mt-5 text-center text-sm text-[var(--curie-text-muted)]">
				Already have an account?
				<a
					class="font-medium text-[var(--curie-blue-l1)] hover:underline"
					href={resolve('/curie/login')}
				>
					Sign in
				</a>
			</p>
		</form>
	</section>
</main>
