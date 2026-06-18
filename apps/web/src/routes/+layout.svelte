<script lang="ts">
	import main_logo from '$lib/assets/main_logo.svg';
	import '../app.css';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={main_logo} />
</svelte:head>

{@render children()}
