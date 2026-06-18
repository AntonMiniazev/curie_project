<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	type Props = {
		autocomplete?: HTMLInputAttributes['autocomplete'];
		label: string;
		minlength?: number;
		required?: boolean;
		type?: 'email' | 'password' | 'text';
		value: string;
	};

	let {
		autocomplete,
		label,
		minlength,
		required = false,
		type = 'text',
		value = $bindable()
	}: Props = $props();
</script>

<label class="mb-4 block">
	<span class="mb-2 block text-sm font-medium text-[var(--curie-text)]">{label}</span>
	<input class="curie-input" {type} {autocomplete} {minlength} {required} bind:value />
</label>
