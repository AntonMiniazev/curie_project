<script lang="ts">
	import { Expand } from '@lucide/svelte';
	import { Handle, type NodeProps } from '@xyflow/svelte';
	import type { FlowNodeData } from '$lib/flow/types';

	let { data }: NodeProps = $props();
	let groupData = $derived(data as FlowNodeData);
	let targetHandles = $derived(groupData.handles?.targets ?? []);
	let sourceHandles = $derived(groupData.handles?.sources ?? []);
	let labelClass = $derived(
		['curie-flow-group-title', groupData.labelClass].filter(Boolean).join(' ')
	);
</script>

{#each targetHandles as handle (`target-${handle.id ?? handle.position}`)}
	<Handle id={handle.id} type="target" position={handle.position} />
{/each}

<div
	class="pointer-events-none absolute inset-0 grid items-start justify-items-center p-2 text-center"
>
	{#if groupData.label}
		<span class={labelClass}>{groupData.label}</span>
	{/if}

	{#if groupData.toggleDetail}
		<span
			class="absolute right-2 top-2 grid h-7 w-7 place-items-center rounded-[var(--curie-radius-xs)] border border-[var(--curie-border)] bg-[var(--curie-control-bg)] text-[var(--curie-blue-l3)] shadow-sm"
			aria-hidden="true"
		>
			<Expand class="h-4 w-4" />
		</span>
	{/if}
</div>

{#each sourceHandles as handle (`source-${handle.id ?? handle.position}`)}
	<Handle id={handle.id} type="source" position={handle.position} />
{/each}
