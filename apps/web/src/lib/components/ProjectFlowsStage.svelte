<script lang="ts">
	import ProjectFlowSection from '$lib/components/ProjectFlowSection.svelte';
	import { projectFlowMeta } from '$lib/data/mainPageFlowMeta';
	import { projectFlows } from '$lib/data/mainPageFlows';

	const projectFlowsById = new Map(projectFlows.map((flow) => [flow.id, flow]));
	const orderedProjectFlows = projectFlowMeta
		.map((flow) => projectFlowsById.get(flow.id))
		.filter((flow) => flow !== undefined);
</script>

{#each orderedProjectFlows as flow (flow.id)}
	<ProjectFlowSection
		id={flow.id}
		name={flow.name}
		description={flow.description}
		nodes={flow.nodes}
		edges={flow.edges}
		detailNodes={flow.detailNodes}
		detailEdges={flow.detailEdges}
	/>
{/each}
