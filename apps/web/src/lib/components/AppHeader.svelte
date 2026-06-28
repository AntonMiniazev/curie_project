<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { Navbar, NavBrand } from 'flowbite-svelte';
	import { onMount } from 'svelte';
	import mainLogo from '$lib/assets/main_logo.svg';
	import FileTextIcon from '~icons/lucide/file-text';
	import GaugeIcon from '~icons/lucide/gauge';
	import MenuIcon from '~icons/lucide/menu';
	import MoonIcon from '~icons/lucide/moon';
	import SunIcon from '~icons/lucide/sun';
	import GithubIcon from '~icons/simple-icons/github';
	import LinkedinIcon from '~icons/simple-icons/linkedin';

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
		if (!supportsHoverMenu()) {
			return;
		}

		clearMenuHoverCloseTimeout();

		if (!isMenuHoverSuppressed) {
			isMenuHovered = true;
		}
	}

	function closeMenuOnHoverEnd() {
		if (!supportsHoverMenu()) {
			return;
		}

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

	function supportsHoverMenu() {
		return window.matchMedia('(hover: hover) and (pointer: fine)').matches;
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

<header bind:this={headerElement} class="curie-header" aria-label={pageName}>
	<Navbar
		fluid
		breakpoint="xl"
		class="curie-header__navbar"
		navContainerClass="curie-page__shell curie-header__container"
	>
		<NavBrand href={resolve('/')} class="curie-header__brand">
			<img class="curie-header__logo" src={mainLogo} alt="Curie home" />
			<span class="curie-header__title">Curie</span>
		</NavBrand>

		<div class="curie-header__spacer" aria-hidden="true"></div>

		<div class="curie-header__controls">
			<button
				class="curie-button curie-button--icon"
				type="button"
				aria-label={theme === 'day' ? 'Switch to night mode' : 'Switch to day mode'}
				aria-pressed={theme === 'night'}
				onclick={toggleTheme}
			>
				{#if theme === 'day'}
					<SunIcon class="h-5 w-5" aria-hidden="true" />
				{:else}
					<MoonIcon class="h-5 w-5" aria-hidden="true" />
				{/if}
			</button>

			<div
				class="curie-header__menu-anchor"
				role="presentation"
				onmouseenter={openMenuOnHover}
				onmouseleave={closeMenuOnHoverEnd}
			>
				<button
					class="curie-button curie-button--icon curie-header__menu-button"
					type="button"
					aria-label={isMenuVisible ? 'Close site menu' : 'Open site menu'}
					aria-expanded={isMenuVisible}
					onclick={toggleMenu}
				>
					<MenuIcon class="h-5 w-5" aria-hidden="true" />
				</button>

				<nav
					class={`curie-header__menu ${isMenuVisible ? 'curie-header__menu--open' : ''}`}
					aria-label="Site menu"
					aria-hidden={!isMenuVisible}
				>
					<ul class="curie-header__menu-list">
						<li>
							<button class="curie-header__menu-action" type="button" onclick={openResume}>
								<FileTextIcon class="h-4 w-4" aria-hidden="true" />
								<span>Resume</span>
							</button>
						</li>
						<li>
							<button class="curie-header__menu-action" type="button" onclick={openBenchmark}>
								<GaugeIcon class="h-4 w-4" aria-hidden="true" />
								<span>Benchmark</span>
							</button>
						</li>
						<li class="curie-header__divider" aria-hidden="true"></li>

						{#each navigationItems as item (item.href)}
							<li>
								<button
									class={`curie-header__menu-action ${selectedHref === item.href ? 'curie-header__menu-action--selected' : ''}`}
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
										class="curie-header__submenu-link"
										type="button"
										onclick={() => navigateTo('/curie/reports/marketing-sales')}
									>
										Marketing
									</button>
								</li>
								<li>
									<button
										class="curie-header__submenu-link"
										type="button"
										onclick={() => navigateTo('/curie/reports/finance-performance')}
									>
										Financial
									</button>
								</li>
								<li>
									<button
										class="curie-header__submenu-link"
										type="button"
										onclick={() => navigateTo('/curie/reports/delivery-operations')}
									>
										Delivery
									</button>
								</li>
							</ul>
						</li>

						<li class="mt-4 border-t border-[var(--curie-border)] px-3 pt-4">
							<div class="curie-header__social-row">
								<a
									class="curie-header__social-link"
									href="https://github.com/antonminiazev"
									target="_blank"
									rel="noreferrer"
									aria-label="Open GitHub profile"
									onclick={closeMenu}
								>
									<GithubIcon class="h-4 w-4" aria-hidden="true" />
								</a>
								<a
									class="curie-header__social-link"
									href="https://www.linkedin.com/in/antonminiazev/"
									target="_blank"
									rel="noreferrer"
									aria-label="Open LinkedIn profile"
									onclick={closeMenu}
								>
									<LinkedinIcon class="h-4 w-4" aria-hidden="true" />
								</a>
							</div>
						</li>
					</ul>
				</nav>
			</div>
		</div>
	</Navbar>
</header>
