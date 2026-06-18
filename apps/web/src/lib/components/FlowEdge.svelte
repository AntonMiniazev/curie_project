<script lang="ts">
	import { BaseEdge, EdgeLabel, getSmoothStepPath, type SmoothStepEdgeProps } from '@xyflow/svelte';
	import type { FlowEdgeData } from '$lib/flow/types';

	let {
		id,
		sourceX,
		sourceY,
		targetX,
		targetY,
		sourcePosition,
		targetPosition,
		markerEnd,
		markerStart,
		label,
		data,
		style,
		pathOptions
	}: SmoothStepEdgeProps & { data?: FlowEdgeData } = $props();

	let [path, labelX, labelY] = $derived(
		getSmoothStepPath({
			sourceX,
			sourceY,
			targetX,
			targetY,
			sourcePosition,
			targetPosition,
			borderRadius: pathOptions?.borderRadius,
			offset: pathOptions?.offset,
			stepPosition: pathOptions?.stepPosition
		})
	);
	let labelVisual = $derived(data?.labelVisual);
	let labelClass = $derived(['curie-flow-edge-label', data?.labelClass].filter(Boolean).join(' '));
</script>

<BaseEdge
	{id}
	{path}
	{markerStart}
	{markerEnd}
	class="curie-flow-edge"
	{style}
	interactionWidth={24}
/>

{#if label}
	<EdgeLabel x={labelX} y={labelY} transparent>
		<span
			class={labelClass}
			style:background-color={labelVisual?.backgroundColor}
			style:border-color={labelVisual?.borderColor}
			style:border-style={labelVisual?.borderStyle}
			style:border-width={labelVisual?.borderWidth}
			style:color={labelVisual?.textColor}
			style:font-size={labelVisual?.fontSize}
		>
			{label}
		</span>
	</EdgeLabel>
{/if}
