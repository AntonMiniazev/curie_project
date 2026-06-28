<script lang="ts">
	import { Gauge, X } from '@lucide/svelte';
	import BenchmarkContent from '$lib/content/benchmark/benchmark.svx';

	type Props = {
		onClose: () => void;
	};

	let { onClose }: Props = $props();

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div
	class="curie-overlay-backdrop fixed inset-0 z-50 bg-[var(--curie-overlay-bg)] px-4 py-5"
	role="dialog"
	aria-modal="true"
	aria-labelledby="benchmark-title"
	tabindex="-1"
>
	<button
		class="absolute inset-0 h-full w-full cursor-default"
		type="button"
		aria-label="Close benchmark"
		onclick={onClose}
	></button>

	<div
		class="relative z-10 mx-auto grid h-full max-w-[var(--curie-page-max-width)] grid-rows-[auto_minmax(0,1fr)] overflow-hidden rounded-[var(--curie-radius-xm)] border border-[var(--curie-border)] bg-[var(--curie-surface)] shadow-xl"
	>
		<header
			class="flex items-center justify-between gap-4 border-b border-[var(--curie-border)] px-5 py-4"
		>
			<div class="flex items-center gap-3">
				<span
					class="grid h-10 w-10 place-items-center rounded-[var(--curie-radius-xm)] border border-[var(--curie-border)] bg-[var(--curie-control-bg)] text-[var(--curie-blue-l3)]"
				>
					<Gauge class="h-5 w-5" aria-hidden="true" />
				</span>
				<div>
					<p class="curie-eyebrow text-xs">Benchmark</p>
					<h2 id="benchmark-title" class="text-xl font-semibold text-[var(--curie-text)]">
						Curie Load Test
					</h2>
				</div>
			</div>

			<button
				class="curie-button grid h-9 w-9 place-items-center hover:text-[var(--curie-red-l1)]"
				type="button"
				aria-label="Close benchmark"
				onclick={onClose}
			>
				<X class="h-4 w-4" aria-hidden="true" />
			</button>
		</header>

		<div class="overflow-y-auto px-5 py-6 md:px-8">
			<div class="curie-resume-content">
				<BenchmarkContent />
			</div>
		</div>
	</div>
</div>
