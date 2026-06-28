<script lang="ts">
	import type { ProjectFlowMeta } from '$lib/data/mainPageFlowMeta';

	type Props = {
		id: string;
		title: string;
		description: string;
		projects?: ProjectFlowMeta[];
		onProjectSelect?: (projectId: string) => void;
	};

	let { id, title, description, projects = [], onProjectSelect }: Props = $props();
</script>

<section
	{id}
	class="grid min-h-full snap-start snap-always place-items-center py-[var(--curie-section-padding-y)]"
	aria-labelledby={`${id}-title`}
>
	<div class="curie-page__shell text-center">
		<h1 id={`${id}-title`} class="text-4xl font-semibold text-[var(--curie-text)] md:text-5xl">
			{title}
		</h1>
		<p class="mx-auto mt-6 max-w-4xl text-lg leading-8 text-[var(--curie-text-muted)]">
			{description}
		</p>

		{#if projects.length > 0}
			<div class="project-intro__project-grid" aria-label="Project sections">
				{#each projects as project (project.id)}
					<button
						class="curie-card curie-card--intro"
						type="button"
						onclick={() => onProjectSelect?.(project.id)}
					>
						<strong class="curie-card__title">{project.name}</strong>
						{#if project.stack}
							<span class="curie-card__meta" aria-hidden={!project.stack}>
								{project.stack ?? ''}
							</span>
						{/if}
						<span class="curie-card__text">{project.description}</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>
</section>
