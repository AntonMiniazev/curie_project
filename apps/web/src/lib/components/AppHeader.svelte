<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { FileText, Moon, Sun } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import mainLogo from '$lib/assets/main_logo.svg';

	type NavigationItem = {
		label: string;
		href: string;
	};

	type Props = {
		pageName: string;
		navigationItems: NavigationItem[];
		selectedHref?: string;
		onResumeOpen?: () => void;
	};

	let { pageName, navigationItems, selectedHref = '/', onResumeOpen }: Props = $props();
	let theme = $state<'day' | 'night'>('day');

	onMount(() => {
		const activeTheme = document.documentElement.dataset.theme;
		theme = activeTheme === 'night' ? 'night' : 'day';
	});

	async function goToNavigationItem(event: Event) {
		const target = event.currentTarget as HTMLSelectElement;

		if (target.value && target.value !== selectedHref) {
			await goto(resolve(target.value as '/' | '/curie'));
		}
	}

	function toggleTheme() {
		applyTheme(theme === 'day' ? 'night' : 'day');
	}

	function applyTheme(nextTheme: 'day' | 'night') {
		theme = nextTheme;
		document.documentElement.dataset.theme = nextTheme;
		localStorage.setItem('curie-theme', nextTheme);
	}
</script>

<header class="border-b border-[var(--curie-border)] bg-[var(--curie-surface)]">
	<div
		class="curie-page-shell grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-4 py-4"
	>
		<a
			class="flex min-w-0 items-center gap-3 justify-self-start font-semibold text-[var(--curie-text)]"
			href={resolve('/')}
		>
			<img class="h-9 w-9" src={mainLogo} alt="Curie home" />
			<span>Curie</span>
		</a>

		<div class="min-w-0 text-center">
			<p
				class="max-w-[16rem] truncate text-sm font-medium text-[var(--curie-text-muted)] md:max-w-[24rem]"
			>
				{pageName}
			</p>
		</div>

		<div class="flex min-w-0 items-center justify-end gap-3">
			{#if onResumeOpen}
				<button
					class="curie-button flex h-10 items-center gap-2 px-3 text-sm hover:text-[var(--curie-blue-l3)]"
					type="button"
					onclick={onResumeOpen}
				>
					<FileText class="h-4 w-4" aria-hidden="true" />
					<span>Resume</span>
				</button>
			{/if}

			<button
				class="grid h-10 w-10 place-items-center rounded-[var(--curie-radius-xm)] border border-[var(--curie-border)] bg-[var(--curie-control-bg)] text-[var(--curie-text)] transition hover:border-[var(--curie-blue-l3)] hover:bg-[var(--curie-control-bg-hover)]"
				type="button"
				aria-label={theme === 'day' ? 'Switch to night mode' : 'Switch to day mode'}
				aria-pressed={theme === 'night'}
				onclick={toggleTheme}
			>
				{#if theme === 'day'}
					<Sun class="h-5 w-5" aria-hidden="true" />
				{:else}
					<Moon class="h-5 w-5" aria-hidden="true" />
				{/if}
			</button>

			<label class="sr-only" for="main-navigation">Navigate to project area</label>
			<select
				id="main-navigation"
				class="curie-select"
				value={selectedHref}
				onchange={goToNavigationItem}
			>
				{#each navigationItems as item (item.href)}
					<option value={item.href}>{item.label}</option>
				{/each}
			</select>
		</div>
	</div>
</header>
