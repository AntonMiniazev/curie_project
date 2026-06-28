<script lang="ts">
	type Props = {
		id: string;
		eyebrow: string;
		title: string;
		description: string;
	};

	let { id, eyebrow, title, description }: Props = $props();
</script>

<section
	{id}
	class="min-h-full snap-start snap-always py-[var(--curie-section-padding-y)]"
	aria-labelledby={`${id}-title`}
>
	<div class="curie-page-shell">
		<p class="curie-eyebrow mb-4">{eyebrow}</p>
		<h1 id={`${id}-title`} class="text-4xl font-semibold text-[var(--curie-text)] md:text-5xl">
			{title}
		</h1>
		<p class="mt-6 text-lg leading-8 text-[var(--curie-text-muted)]">{description}</p>
	</div>
</section>
