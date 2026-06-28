<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { FileText, Gauge, Menu, Moon, Sun } from '@lucide/svelte';
	import { Navbar, NavBrand } from 'flowbite-svelte';
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
		onBenchmarkOpen?: () => void;
	};

	let {
		pageName,
		navigationItems,
		selectedHref = '/',
		onResumeOpen,
		onBenchmarkOpen
	}: Props = $props();
	let theme = $state<'day' | 'night'>('day');
	let isMenuOpen = $state(false);
	let isMenuHovered = $state(false);
	let isMenuHoverSuppressed = $state(false);
	let headerElement = $state<HTMLElement | null>(null);
	let menuHoverCloseTimeout: ReturnType<typeof setTimeout> | null = null;
	const isMenuVisible = $derived(isMenuOpen || (isMenuHovered && !isMenuHoverSuppressed));
	const menuHoverCloseDelayMs = 500;

	onMount(() => {
		const activeTheme = document.documentElement.dataset.theme;
		theme = activeTheme === 'night' ? 'night' : 'day';

		function handleDocumentClick(event: MouseEvent) {
			if (!isMenuVisible || headerElement?.contains(event.target as Node)) {
				return;
			}

			closeMenu();
		}

		document.addEventListener('click', handleDocumentClick);

		return () => {
			document.removeEventListener('click', handleDocumentClick);
			clearMenuHoverCloseTimeout();
		};
	});

	function toggleTheme() {
		applyTheme(theme === 'day' ? 'night' : 'day');
	}

	function toggleMenu() {
		if (isMenuVisible) {
			closeMenu();
			isMenuHoverSuppressed = true;
			return;
		}

		isMenuOpen = true;
		isMenuHoverSuppressed = false;
	}

	function closeMenu() {
		clearMenuHoverCloseTimeout();
		isMenuOpen = false;
		isMenuHovered = false;
	}

	function openMenuOnHover() {
		clearMenuHoverCloseTimeout();

		if (!isMenuHoverSuppressed) {
			isMenuHovered = true;
		}
	}

	function closeMenuOnHoverEnd() {
		isMenuHoverSuppressed = false;
		clearMenuHoverCloseTimeout();
		menuHoverCloseTimeout = setTimeout(() => {
			isMenuHovered = false;
			isMenuOpen = false;
			menuHoverCloseTimeout = null;
		}, menuHoverCloseDelayMs);
	}

	function clearMenuHoverCloseTimeout() {
		if (!menuHoverCloseTimeout) {
			return;
		}

		clearTimeout(menuHoverCloseTimeout);
		menuHoverCloseTimeout = null;
	}

	async function openResume() {
		closeMenu();

		if (onResumeOpen) {
			onResumeOpen();
			return;
		}

		await goto(resolve('/?resume=open'));
	}

	async function openBenchmark() {
		closeMenu();

		if (onBenchmarkOpen) {
			onBenchmarkOpen();
			return;
		}

		await goto(resolve('/?benchmark=open'));
	}

	async function navigateTo(href: string) {
		closeMenu();
		await goto(resolve(href as '/' | '/curie' | `/curie/reports/${string}`));
	}

	function applyTheme(nextTheme: 'day' | 'night') {
		theme = nextTheme;
		document.documentElement.dataset.theme = nextTheme;
		localStorage.setItem('curie-theme', nextTheme);
	}
</script>

<header bind:this={headerElement} class="curie-app-header" aria-label={pageName}>
	<Navbar
		fluid
		breakpoint="xl"
		class="curie-navbar-root"
		navContainerClass="curie-page-shell curie-navbar-container"
	>
		<NavBrand href={resolve('/')} class="curie-navbar-brand">
			<img class="curie-navbar-logo" src={mainLogo} alt="Curie home" />
			<span class="curie-navbar-title">Curie</span>
		</NavBrand>

		<div class="curie-navbar-spacer" aria-hidden="true"></div>

		<div class="curie-navbar-controls">
			<button
				class="curie-icon-button"
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

			<div
				class="curie-navbar-menu-anchor"
				role="presentation"
				onmouseenter={openMenuOnHover}
				onmouseleave={closeMenuOnHoverEnd}
			>
				<button
					class="curie-icon-button curie-navbar-menu-button"
					type="button"
					aria-label={isMenuVisible ? 'Close site menu' : 'Open site menu'}
					aria-expanded={isMenuVisible}
					onclick={toggleMenu}
				>
					<Menu class="h-5 w-5" aria-hidden="true" />
				</button>

				<nav
					class:curie-navbar-menu-open={isMenuVisible}
					class="curie-navbar-menu"
					aria-label="Site menu"
					aria-hidden={!isMenuVisible}
				>
					<ul class="curie-navbar-menu-list">
						{#each navigationItems as item (item.href)}
							<li>
								<button
									class:selected={selectedHref === item.href}
									class="curie-navbar-action"
									type="button"
									onclick={() => navigateTo(item.href)}
								>
									{item.label}
								</button>
							</li>
						{/each}		
						<li class="px-3 pt-2">
							<ul class="space-y-1">
								<li>
									<button
										class="curie-navbar-sub-link"
										type="button"
										onclick={() => navigateTo('/curie/reports/marketing-sales')}
									>
										Marketing
									</button>
								</li>
								<li>
									<button
										class="curie-navbar-sub-link"
										type="button"
										onclick={() => navigateTo('/curie/reports/finance-performance')}
									>
										Financial
									</button>
								</li>
								<li>
									<button
										class="curie-navbar-sub-link"
										type="button"
										onclick={() => navigateTo('/curie/reports/delivery-operations')}
									>
										Delivery
									</button>
								</li>
							</ul>
						</li>						
						<li class="curie-navbar-section-line" aria-hidden="true"></li>			
						<li>
							<button class="curie-navbar-action" type="button" onclick={openResume}>
								<FileText class="h-4 w-4" aria-hidden="true" />
								<span>Resume</span>
							</button>
						</li>
						<li>
							<button class="curie-navbar-action" type="button" onclick={openBenchmark}>
								<Gauge class="h-4 w-4" aria-hidden="true" />
								<span>Benchmark</span>
							</button>
						</li>

						<li class="mt-4 border-t border-[var(--curie-border)] px-3 pt-4">
							<div class="curie-navbar-social-row">
								<a
									class="curie-navbar-social-link"
									href="https://github.com/antonminiazev"
									target="_blank"
									rel="noreferrer"
									aria-label="Open GitHub profile"
									onclick={closeMenu}
								>
									<svg viewBox="0 0 24 24" class="h-4 w-4" aria-hidden="true">
										<path
											fill="currentColor"
											d="M12 2A10 10 0 0 0 8.84 21.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.2-3.37-1.2a2.65 2.65 0 0 0-1.11-1.46c-.91-.62.07-.61.07-.61a2.1 2.1 0 0 1 1.53 1.03 2.13 2.13 0 0 0 2.91.83 2.12 2.12 0 0 1 .63-1.34c-2.22-.25-4.56-1.11-4.56-4.94a3.87 3.87 0 0 1 1.03-2.69 3.6 3.6 0 0 1 .1-2.65s.84-.27 2.75 1.03a9.47 9.47 0 0 1 5 0c1.91-1.3 2.75-1.03 2.75-1.03a3.6 3.6 0 0 1 .1 2.65 3.86 3.86 0 0 1 1.03 2.69c0 3.84-2.34 4.68-4.57 4.93a2.38 2.38 0 0 1 .68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"
										/>
									</svg>
								</a>
								<a
									class="curie-navbar-social-link"
									href="https://www.linkedin.com/"
									target="_blank"
									rel="noreferrer"
									aria-label="Open LinkedIn profile"
									onclick={closeMenu}
								>
									<svg viewBox="0 0 24 24" class="h-4 w-4" aria-hidden="true">
										<path
											fill="currentColor"
											d="M5.34 8.74H2.67v12.25h2.67V8.74ZM4 3.01a1.54 1.54 0 1 0 0 3.08 1.54 1.54 0 0 0 0-3.08ZM21.33 14.34c0-3.29-1.76-4.82-4.11-4.82a3.54 3.54 0 0 0-3.2 1.76h-.04V9.78h-2.56v11.21h2.67v-5.55c0-1.46.28-2.88 2.09-2.88 1.78 0 1.8 1.67 1.8 2.97v5.46h2.67l.68-6.65Z"
										/>
									</svg>
								</a>
							</div>
						</li>
					</ul>
				</nav>
			</div>
		</div>
	</Navbar>
</header>
