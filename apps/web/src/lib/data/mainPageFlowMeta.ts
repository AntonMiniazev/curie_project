export type ProjectFlowMeta = {
	id: string;
	name: string;
	description: string;
	repositoryUrl: string;
	stack?: string;
};

export const projectFlowMeta: ProjectFlowMeta[] = [
	{
		id: 'ampere',
		name: 'Ampere',
		repositoryUrl: 'https://github.com/antonminiazev/ampere_project',
		stack: 'Apache Iceberg, Python (PySpark, DuckDB), Airflow, dbt, Lakekeeper',
		description:
			'Data platform project: synthetic operational data is generated, landed, transformed through Bronze/Silver/Gold layers, governed through Lakekeeper, and served to BI consumers.'
	},
	{
		id: 'bohr',
		name: 'Bohr',
		repositoryUrl: 'https://github.com/antonminiazev/bohr_project',
		stack: 'Kubernetes, Terraform, Helm',
		description:
			'Infrastructure project: home lab Ubuntu server with Kubernetes cluster, Hetzner server and deployment automation are documented as a connected operating model.'
	},
	{
		id: 'curie',
		name: 'Curie',
		repositoryUrl: 'https://github.com/antonminiazev/curie_project',
		stack: 'FastAPI, SvelteKit, Streamlit',
		description:
			'Reporting application project: authenticated SvelteKit frontend and FastAPI backend expose governed reports backed by a DuckDB cache refreshed from Ampere Gold through Flight SQL.'
	}
];
