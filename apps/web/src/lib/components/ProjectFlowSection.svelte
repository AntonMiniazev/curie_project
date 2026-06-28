<script lang="ts">
	import { fade, scale } from 'svelte/transition';
	import {
		Background,
		BackgroundVariant,
		Controls,
		SvelteFlow,
		type Edge,
		type Node,
		type NodeEventWithPointer
	} from '@xyflow/svelte';
	import { Expand, RotateCcw } from '@lucide/svelte';
	import FlowEdge from '$lib/components/FlowEdge.svelte';
	import FlowGroupNode from '$lib/components/FlowGroupNode.svelte';
	import FlowNode from '$lib/components/FlowNode.svelte';
	import type { FlowNodeData } from '$lib/flow/types';

	const nodeTypes = {
		default: FlowNode,
		input: FlowNode,
		output: FlowNode,
		group: FlowGroupNode
	};

	const edgeTypes = {
		curie: FlowEdge
	};
	const proOptions = {
		hideAttribution: true
	};

	type Props = {
		id: string;
		name: string;
		description: string;
		nodes: Node<FlowNodeData>[];
		edges: Edge[];
		detailNodes?: Node<FlowNodeData>[];
		detailEdges?: Edge[];
	};

	let { id, name, description, nodes, edges, detailNodes = [], detailEdges = [] }: Props = $props();

	let showDetail = $state(false);
	let isExpanded = $state(false);
	let flowViewKey = $state(0);
	let renderedNodes = $derived(showDetail && detailNodes.length > 0 ? detailNodes : nodes);
	let renderedEdges = $derived(showDetail && detailEdges.length > 0 ? detailEdges : edges);

	const handleNodeClick: NodeEventWithPointer<
		MouseEvent | TouchEvent,
		Node<FlowNodeData>
	> = async ({ node }) => {
		if (node.data.toggleDetail && detailNodes.length > 0) {
			showDetail = true;
			flowViewKey += 1;
			return;
		}

		if (node.data.scrollTarget) {
			document.querySelector(node.data.scrollTarget)?.scrollIntoView({ behavior: 'smooth' });
		}
	};

	function resetFlowView() {
		showDetail = false;
		flowViewKey += 1;
	}

	function closeExpandedFlow() {
		isExpanded = false;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function handleWindowKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isExpanded) {
			closeExpandedFlow();
		}
	}
</script>

<svelte:window onkeydown={handleWindowKeydown} />
<svelte:body class:overflow-hidden={isExpanded} />

<section
	{id}
	class="grid min-h-full snap-start snap-always grid-rows-[auto_minmax(22rem,1fr)] gap-5 py-[var(--curie-section-padding-y)]"
	aria-labelledby={`${id}-title`}
>
	<header
		class="curie-page-shell flex flex-col gap-4 md:flex-row md:items-start md:justify-between"
	>
		<div>
			<h2 id={`${id}-title`} class="text-4xl font-semibold text-[var(--curie-text)]">
				<span class="text-[var(--curie-blue-l3)]">Project</span>
				{name}
			</h2>
			<p class="mt-2 max-w-3xl leading-7 text-[var(--curie-text-muted)]">{description}</p>
		</div>
	</header>

	<div
		class="curie-card curie-flow-card curie-page-shell relative h-full min-h-[22rem] overflow-hidden"
	>
		{#if showDetail}
			<button
				class="curie-button absolute right-14 top-3 z-40 grid h-9 w-9 place-items-center bg-[var(--curie-control-bg)]/90 shadow-sm backdrop-blur hover:text-[var(--curie-blue-l3)]"
				type="button"
				aria-label={`Reset ${name} diagram`}
				title={`Reset ${name} diagram`}
				onclick={resetFlowView}
			>
				<RotateCcw class="h-4 w-4" aria-hidden="true" />
			</button>
		{/if}

		<button
			class="curie-button absolute right-3 top-3 z-40 grid h-9 w-9 place-items-center bg-[var(--curie-control-bg)]/90 shadow-sm backdrop-blur hover:text-[var(--curie-blue-l3)]"
			type="button"
			aria-label={`Expand ${name} diagram`}
			title={`Expand ${name} diagram`}
			onclick={() => (isExpanded = true)}
		>
			<Expand class="h-4 w-4" aria-hidden="true" />
		</button>

		{#key flowViewKey}
			<SvelteFlow
				nodes={renderedNodes}
				edges={renderedEdges}
				fitView
				nodesDraggable={false}
				nodesConnectable={false}
				elementsSelectable={false}
				preventScrolling={false}
				zoomOnScroll={false}
				zoomOnPinch={false}
				zIndexMode="manual"
				{proOptions}
				{nodeTypes}
				{edgeTypes}
				onnodeclick={handleNodeClick}
			>
				<Controls />
				<Background variant={BackgroundVariant.Dots} />
			</SvelteFlow>
		{/key}
	</div>

	{#if isExpanded}
		<div
			class="curie-overlay-backdrop fixed inset-0 z-50 grid grid-rows-[auto_minmax(0,1fr)] gap-4 bg-[var(--curie-overlay-bg)] px-5 py-5"
			role="dialog"
			aria-modal="true"
			aria-labelledby={`${id}-expanded-title`}
			onwheel={(event) => event.stopPropagation()}
			transition:fade={{ duration: 180 }}
		>
			<header
				class="mx-auto flex w-full max-w-[94rem] items-center justify-between gap-4 rounded-[var(--curie-radius-xm)] border border-[var(--curie-border)] bg-[var(--curie-control-bg)]/90 px-4 py-3 shadow-sm"
				transition:scale={{ duration: 220, start: 0.98 }}
			>
				<div class="min-w-0">
					<p class="curie-eyebrow text-xs">Expanded diagram</p>
					<h3
						id={`${id}-expanded-title`}
						class="truncate text-lg font-semibold text-[var(--curie-text)]"
					>
						Project {name}
					</h3>
				</div>

				<div class="flex items-center gap-2">
					{#if showDetail}
						<button
							class="curie-button grid h-9 w-9 place-items-center hover:text-[var(--curie-blue-l3)]"
							type="button"
							aria-label={`Reset ${name} diagram`}
							title={`Reset ${name} diagram`}
							onclick={resetFlowView}
						>
							<RotateCcw class="h-4 w-4" aria-hidden="true" />
						</button>
					{/if}

					<button
						class="curie-button px-3 py-2 text-sm hover:border-[var(--curie-red-l1)] hover:text-[var(--curie-red-l1)]"
						type="button"
						onclick={closeExpandedFlow}
					>
						Close
					</button>
				</div>
			</header>

			<div
				class="curie-card curie-flow-card mx-auto min-h-0 w-full max-w-[94rem] overflow-hidden shadow-xl"
				transition:scale={{ duration: 240, start: 0.96 }}
			>
				{#key flowViewKey}
					<SvelteFlow
						nodes={renderedNodes}
						edges={renderedEdges}
						fitView
						nodesDraggable={false}
						nodesConnectable={false}
						elementsSelectable={false}
						preventScrolling={false}
						zoomOnScroll={false}
						zoomOnPinch={false}
						zIndexMode="manual"
						{proOptions}
						{nodeTypes}
						{edgeTypes}
						onnodeclick={handleNodeClick}
					>
						<Controls />
						<Background variant={BackgroundVariant.Dots} />
					</SvelteFlow>
				{/key}
			</div>
		</div>
	{/if}
</section>
