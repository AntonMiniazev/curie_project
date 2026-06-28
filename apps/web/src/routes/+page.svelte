<script lang="ts">
	import type { Component } from 'svelte';
	import { resolve } from '$app/paths';
	import { onMount, tick } from 'svelte';

	import AppHeader from '$lib/components/AppHeader.svelte';
	import BenchmarkOverlay from '$lib/components/BenchmarkOverlay.svelte';
	import MainIntroSection from '$lib/components/MainIntroSection.svelte';
	import ResumeOverlay from '$lib/components/ResumeOverlay.svelte';
	import { projectFlowMeta } from '$lib/data/mainPageFlowMeta';
	import { mainNavigationItems } from '$lib/navigation';

	const sectionNavigation = [
		{ id: 'introduction', label: 'Introduction' },
		...projectFlowMeta.map((flow) => ({ id: flow.id, label: flow.name }))
	];
	const sectionScrollDurationMs = 650;
	const wheelGestureThreshold = 100;
	const wheelGestureResetMs = 120;
	const wheelTransitionCooldownMs = 300;

	let scrollContainer = $state<HTMLElement | null>(null);
	let activeSectionId = $state(sectionNavigation[0].id);
	let isAnimatingScroll = $state(false);
	let isBenchmarkOpen = $state(false);
	let isResumeOpen = $state(false);
	let hasMounted = $state(false);
	let ProjectFlowsStage = $state<Component | null>(null);
	let wheelDeltaAccumulator = 0;
	let wheelResetTimeout: ReturnType<typeof setTimeout> | null = null;
	let wheelCooldownUntil = 0;
	let sectionObserver: IntersectionObserver | null = null;

	onMount(() => {
		if (!scrollContainer) {
			return;
		}

		if (window.location.search.includes('resume=open')) {
			isResumeOpen = true;
			window.history.replaceState(null, '', resolve('/'));
		}

		if (window.location.search.includes('benchmark=open')) {
			isBenchmarkOpen = true;
			window.history.replaceState(null, '', resolve('/'));
		}

		document.documentElement.style.setProperty(
			'--curie-scrollbar-width',
			`${measureScrollbarWidth()}px`
		);
		document.body.classList.add('project-hub');
		hasMounted = true;
		void initializeClientSections();

		scrollContainer.addEventListener('wheel', handleWheelScroll, { passive: false });

		return () => {
			sectionObserver?.disconnect();
			scrollContainer?.removeEventListener('wheel', handleWheelScroll);
			document.body.classList.remove('project-hub');
			document.documentElement.style.removeProperty('--curie-scrollbar-width');
		};
	});

	async function initializeClientSections() {
		await tick();
		observeSections();
		requestAnimationFrame(() => {
			void loadProjectFlowsStage();
		});
	}

	async function loadProjectFlowsStage() {
		const module = await import('$lib/components/ProjectFlowsStage.svelte');
		ProjectFlowsStage = module.default;
		await tick();
		observeSections();
	}

	function observeSections() {
		if (!scrollContainer) {
			return;
		}

		sectionObserver?.disconnect();
		sectionObserver = new IntersectionObserver(
			(entries) => {
				const activeEntry = entries
					.filter((entry) => entry.isIntersecting)
					.sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

				if (activeEntry) {
					activeSectionId = activeEntry.target.id;
				}
			},
			{
				root: scrollContainer,
				threshold: [0.55, 0.75, 0.95]
			}
		);

		for (const section of sectionNavigation) {
			const element = document.getElementById(section.id);
			if (element) {
				sectionObserver.observe(element);
			}
		}
	}

	function scrollToSection(sectionId: string) {
		animateToSection(sectionId);
	}

	function handleWheelScroll(event: WheelEvent) {
		event.preventDefault();

		const currentTime = performance.now();

		if (isAnimatingScroll || currentTime < wheelCooldownUntil) {
			resetWheelGesture();
			return;
		}

		wheelDeltaAccumulator += normalizeWheelDelta(event);
		restartWheelGestureReset();

		if (Math.abs(wheelDeltaAccumulator) < wheelGestureThreshold) {
			return;
		}

		const activeIndex = sectionNavigation.findIndex((section) => section.id === activeSectionId);
		const direction = wheelDeltaAccumulator > 0 ? 1 : -1;
		const targetIndex = Math.max(
			0,
			Math.min(sectionNavigation.length - 1, activeIndex + direction)
		);

		resetWheelGesture();

		if (targetIndex !== activeIndex) {
			animateToSection(sectionNavigation[targetIndex].id);
		}
	}

	function animateToSection(sectionId: string) {
		if (!scrollContainer) {
			return;
		}

		const targetElement = document.getElementById(sectionId);
		if (!targetElement) {
			return;
		}

		const startTop = scrollContainer.scrollTop;
		const targetTop = getTargetScrollTop(targetElement);
		const distance = targetTop - startTop;
		const startTime = performance.now();

		isAnimatingScroll = true;

		function animateFrame(currentTime: number) {
			if (!scrollContainer) {
				isAnimatingScroll = false;
				return;
			}

			const elapsed = currentTime - startTime;
			const progress = Math.min(elapsed / sectionScrollDurationMs, 1);
			const easedProgress = easeInOutCubic(progress);

			scrollContainer.scrollTop = startTop + distance * easedProgress;

			if (progress < 1) {
				requestAnimationFrame(animateFrame);
				return;
			}

			scrollContainer.scrollTop = targetTop;
			activeSectionId = sectionId;
			isAnimatingScroll = false;
			wheelCooldownUntil = performance.now() + wheelTransitionCooldownMs;
		}

		requestAnimationFrame(animateFrame);
	}

	function normalizeWheelDelta(event: WheelEvent) {
		if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) {
			return event.deltaY * 16;
		}

		if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE && scrollContainer) {
			return event.deltaY * scrollContainer.clientHeight;
		}

		return event.deltaY;
	}

	function restartWheelGestureReset() {
		if (wheelResetTimeout) {
			clearTimeout(wheelResetTimeout);
		}

		wheelResetTimeout = setTimeout(resetWheelGesture, wheelGestureResetMs);
	}

	function resetWheelGesture() {
		wheelDeltaAccumulator = 0;

		if (wheelResetTimeout) {
			clearTimeout(wheelResetTimeout);
			wheelResetTimeout = null;
		}
	}

	function getTargetScrollTop(targetElement: HTMLElement) {
		if (!scrollContainer) {
			return 0;
		}

		const containerRect = scrollContainer.getBoundingClientRect();
		const targetRect = targetElement.getBoundingClientRect();

		return scrollContainer.scrollTop + targetRect.top - containerRect.top;
	}

	function easeInOutCubic(value: number) {
		return value < 0.5 ? 4 * value * value * value : 1 - Math.pow(-2 * value + 2, 3) / 2;
	}

	function measureScrollbarWidth() {
		const element = document.createElement('div');
		element.style.position = 'absolute';
		element.style.top = '-9999px';
		element.style.width = '100px';
		element.style.height = '100px';
		element.style.overflow = 'scroll';
		document.body.appendChild(element);

		const scrollbarWidth = element.offsetWidth - element.clientWidth;
		element.remove();

		return scrollbarWidth;
	}
</script>

<svelte:body class:overflow-hidden={isResumeOpen || isBenchmarkOpen} />

<div class="curie-page h-screen overflow-hidden bg-[var(--curie-bg)]">
	<AppHeader
		pageName="Project hub"
		navigationItems={mainNavigationItems}
		selectedHref="/"
		onResumeOpen={() => (isResumeOpen = true)}
		onBenchmarkOpen={() => (isBenchmarkOpen = true)}
	/>

	<main
		bind:this={scrollContainer}
		data-project-scroll-container
		class="h-[calc(100vh-4.5rem)] overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden {isAnimatingScroll
			? 'snap-none'
			: 'snap-y snap-mandatory'}"
	>
		<MainIntroSection
			id="introduction"
			title="A practical full-stack lab for data platforms, infrastructure, and reporting apps."
			description="This website is the public entry point for the projects I am building for learning modern full-stack development. Combination of resources is inefficient as main purpose is learning through practice. Each section documents one project and links the architecture to the running application."
			projects={projectFlowMeta}
			onProjectSelect={scrollToSection}
		/>

		{#if ProjectFlowsStage}
			<ProjectFlowsStage />
		{:else if hasMounted}
			{#each projectFlowMeta as flow (flow.id)}
				<section
					id={flow.id}
					class="grid min-h-full snap-start snap-always grid-rows-[auto_minmax(22rem,1fr)] gap-5 py-[var(--curie-section-padding-y)]"
					aria-labelledby={`${flow.id}-title`}
				>
					<header
						class="curie-page__shell flex flex-col gap-4 md:flex-row md:items-start md:justify-between"
					>
						<div>
							<h2 id={`${flow.id}-title`} class="text-4xl font-semibold text-[var(--curie-text)]">
								<!-- eslint-disable svelte/no-navigation-without-resolve -->
								<a
									class="project-flow__title-link"
									href={flow.repositoryUrl}
									target="_blank"
									rel="noreferrer"
								>
									<span class="text-[var(--curie-blue-l3)]">Project</span>
									{flow.name}
								</a>
								<!-- eslint-enable svelte/no-navigation-without-resolve -->
							</h2>
							<p class="mt-2 max-w-3xl leading-7 text-[var(--curie-text-muted)]">
								{flow.description}
							</p>
						</div>
					</header>

					<div
						class="curie-card curie-card--flow curie-page__shell grid h-full min-h-[22rem] place-items-center overflow-hidden text-sm text-[var(--curie-text-muted)]"
					>
						Loading {flow.name} diagram...
					</div>
				</section>
			{/each}
		{/if}
	</main>

	<nav
		class="fixed right-5 top-1/2 z-20 flex -translate-y-1/2 flex-col gap-3"
		aria-label="Main page sections"
	>
		{#each sectionNavigation as section (section.id)}
			<button
				class="h-3 w-3 rounded-full border border-[var(--curie-border)] transition-colors {activeSectionId ===
				section.id
					? 'bg-[var(--curie-blue-l1)]'
					: 'bg-[var(--curie-border)]'}"
				type="button"
				aria-label={`Scroll to ${section.label}`}
				aria-current={activeSectionId === section.id ? 'step' : undefined}
				onclick={() => scrollToSection(section.id)}
			></button>
		{/each}
	</nav>

	{#if isResumeOpen}
		<ResumeOverlay onClose={() => (isResumeOpen = false)} />
	{/if}

	{#if isBenchmarkOpen}
		<BenchmarkOverlay onClose={() => (isBenchmarkOpen = false)} />
	{/if}
</div>
