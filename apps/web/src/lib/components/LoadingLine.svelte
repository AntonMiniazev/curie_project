<script lang="ts">
	type Props = {
		label?: string;
	};

	let { label = 'Loading...' }: Props = $props();
</script>

<div
	class="flex items-center justify-center gap-3 py-16 text-sm font-medium text-[var(--curie-text-muted)]"
>
	<span
		class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--curie-border)] border-t-[var(--curie-blue-l3)]"
		aria-hidden="true"
	></span>
	<span>{label}</span>
</div>
