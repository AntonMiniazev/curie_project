export type ProjectFlowMeta = {
	id: string;
	name: string;
	description: string;
};

export const projectFlowMeta: ProjectFlowMeta[] = [
	{
		id: 'ampere',
		name: 'Ampere',
		description:
			'Data platform project: synthetic operational data is generated, landed, transformed through Bronze/Silver/Gold layers, governed through Unity Catalog OSS, and served to BI consumers.'
	},
	{
		id: 'bohr',
		name: 'Bohr',
		description:
			'Infrastructure project: local workstation, Hetzner server, home lab, Kubernetes services, and deployment automation are documented as a connected operating model.'
	},
	{
		id: 'curie',
		name: 'Curie',
		description:
			'Reporting application project: authenticated SvelteKit frontend and FastAPI backend expose governed reports backed by a parquet cache refreshed from the Ampere gold layer.'
	}
];
