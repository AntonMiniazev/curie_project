<script lang="ts">
	import { Handle, Position, type NodeProps } from '@xyflow/svelte';
	import type { FlowHandleConfig, FlowNodeData } from '$lib/flow/types';

	let {
		data,
		type,
		sourcePosition = Position.Right,
		targetPosition = Position.Left
	}: NodeProps = $props();

	let nodeData = $derived(data as FlowNodeData);
	let isInput = $derived(type === 'input');
	let isOutput = $derived(type === 'output');
	let handlesDisabled = $derived(Boolean(nodeData.disableHandles));
	let targetHandles = $derived(
		getHandles(nodeData.handles?.targets, targetPosition, isInput || handlesDisabled)
	);
	let sourceHandles = $derived(
		getHandles(nodeData.handles?.sources, sourcePosition, isOutput || handlesDisabled)
	);
	let labelClass = $derived(
		['project-flow__node-label', nodeData.labelClass].filter(Boolean).join(' ')
	);
	let secondaryLabelClass = $derived(
		['project-flow__node-secondary-label', nodeData.secondaryLabelClass].filter(Boolean).join(' ')
	);

	function getHandles(
		configuredHandles: FlowHandleConfig[] | undefined,
		fallbackPosition: Position,
		disabled: boolean
	) {
		if (disabled) {
			return [];
		}

		return configuredHandles?.length ? configuredHandles : [{ position: fallbackPosition }];
	}
</script>

{#each targetHandles as handle (`target-${handle.id ?? handle.position}`)}
	<Handle id={handle.id} type="target" position={handle.position} />
{/each}

<div class="flex h-full w-full items-center justify-center overflow-hidden text-center">
	<span class="project-flow__node-text">
		<span class={labelClass}>{nodeData.label}</span>
		{#if nodeData.secondaryLabel}
			<span class={secondaryLabelClass}>{nodeData.secondaryLabel}</span>
		{/if}
	</span>
</div>

{#each sourceHandles as handle (`source-${handle.id ?? handle.position}`)}
	<Handle id={handle.id} type="source" position={handle.position} />
{/each}
