<script lang="ts">
	import { asset } from '$app/paths';
	import { FileDown, X } from '@lucide/svelte';
	import ResumeContent from '$lib/content/resume/mock-resume.svx';

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
	class="fixed inset-0 z-50 bg-[var(--curie-overlay-bg)] px-4 py-5 backdrop-blur-md"
	role="dialog"
	aria-modal="true"
	aria-labelledby="resume-title"
	tabindex="-1"
>
	<button
		class="absolute inset-0 h-full w-full cursor-default"
		type="button"
		aria-label="Close resume"
		onclick={onClose}
	></button>

	<div
		class="relative z-10 mx-auto grid h-full max-w-[var(--curie-page-max-width)] grid-rows-[auto_minmax(0,1fr)] overflow-hidden rounded-[var(--curie-radius-xm)] border border-[var(--curie-border)] bg-[var(--curie-surface)] shadow-xl"
	>
		<header
			class="flex items-center justify-between gap-4 border-b border-[var(--curie-border)] px-5 py-4"
		>
			<div>
				<p class="curie-eyebrow text-xs">Resume</p>
				<h2 id="resume-title" class="text-xl font-semibold text-[var(--curie-text)]">
					Anton Miniazev
				</h2>
			</div>

			<div class="flex items-center gap-2">
				<a
					class="curie-button grid h-9 w-9 place-items-center hover:text-[var(--curie-blue-l3)]"
					href={asset('/resume.pdf')}
					download="anton-miniazev-resume.pdf"
					aria-label="Download resume PDF"
					title="Download resume PDF"
				>
					<FileDown class="h-4 w-4" aria-hidden="true" />
				</a>

				<button
					class="curie-button grid h-9 w-9 place-items-center hover:text-[var(--curie-red-l1)]"
					type="button"
					aria-label="Close resume"
					onclick={onClose}
				>
					<X class="h-4 w-4" aria-hidden="true" />
				</button>
			</div>
		</header>

		<div class="overflow-y-auto px-5 py-6 md:px-8">
			<div class="curie-resume-content">
				<ResumeContent />
			</div>
		</div>
	</div>
</div>
