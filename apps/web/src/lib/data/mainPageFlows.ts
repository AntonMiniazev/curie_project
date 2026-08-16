import { MarkerType, Position, type Edge, type Node } from '@xyflow/svelte';
import type { FlowEdgeData, FlowNodeData } from '$lib/flow/types';

export type ProjectFlow = {
	id: string;
	name: string;
	description: string;
	nodes: Node<FlowNodeData>[];
	edges: Edge<FlowEdgeData>[];
	detailNodes?: Node<FlowNodeData>[];
	detailEdges?: Edge<FlowEdgeData>[];
};

const defaultEdgeOptions = {
	type: 'curie',
	zIndex: 30,
	animated: true,
	markerEnd: {
		type: MarkerType.ArrowClosed
	}
} satisfies Partial<Edge<FlowEdgeData>>;

const groupStyle = (width: number, height: number) =>
	[`width: ${width}px;`, `height: ${height}px;`].join(' ');

export const projectFlows: ProjectFlow[] = [
	{
		id: 'ampere',
		name: 'Ampere',
		description:
			'Data platform project: synthetic operational data is generated, landed, transformed through Bronze/Silver/Gold layers, governed through Unity Catalog OSS, and served to BI consumers.',
		nodes: [
			{
				id: '1-1',
				type: 'group',
				position: {
					x: 0,
					y: 0
				},
				data: { label: 'Homelab platform orchestrated via Airflow' },
				style: groupStyle(1050, 450),
				zIndex: 0
			},
			{
				id: '1-2',
				type: 'group',
				position: {
					x: 50,
					y: 100
				},
				data: { label: 'Data generation and Raw layer' },
				style: groupStyle(300, 300),
				zIndex: 0
			},
			{
				id: '2-2',
				type: 'group',
				position: {
					x: 400,
					y: 100
				},
				data: { label: 'Delta Lakehouse on MinIO with Unity Catalog OSS' },
				style: groupStyle(600, 300),
				zIndex: 0
			},
			{
				id: '3-2',
				type: 'group',
				position: {
					x: 1100,
					y: 100
				},
				data: { label: 'Frontend on Hetzner server' },
				style: groupStyle(300, 300),
				zIndex: 0
			},
			{
				id: 'ampere-source',
				type: 'input',
				data: { label: 'Python generator to PostgreSQL job' },
				position: { x: 137.5, y: 170 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Left,
				parentId: '1-1',
				zIndex: 20
			},
			{
				id: 'ampere-raw',
				data: { label: 'Raw landing\nMinIO parquet batches' },
				position: { x: 137.5, y: 300 },
				sourcePosition: Position.Right,
				targetPosition: Position.Top,
				zIndex: 20
			},
			{
				id: 'ampere-bronze',
				data: { label: 'Bronze Layer' },
				position: { x: 456.25, y: 170 },
				sourcePosition: Position.Right,
				targetPosition: Position.Left,
				zIndex: 20
			},
			{
				id: 'ampere-silver',
				data: { label: 'Silver\ndbt cleaned reusable tables' },
				position: { x: 637.5, y: 300 },
				sourcePosition: Position.Right,
				targetPosition: Position.Left,
				zIndex: 20
			},
			{
				id: 'ampere-gold',
				data: { label: 'Gold\nBI aggregates' },
				position: { x: 818.75, y: 170 },
				sourcePosition: Position.Right,
				targetPosition: Position.Left,
				zIndex: 20
			},
			{
				id: 'ampere-cache',
				data: { label: 'Local cache' },
				position: { x: 1187.5, y: 170 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Left,
				zIndex: 20
			},
			{
				id: 'ampere-streamlit',
				type: 'output',
				data: { label: 'Streamlit Apps' },
				position: { x: 1187.5, y: 300 },
				sourcePosition: Position.Right,
				targetPosition: Position.Top,
				zIndex: 20
			}
		],
		edges: [
			{
				id: 'ampere-source-raw',
				source: 'ampere-source',
				target: 'ampere-raw',
				label: 'Spark extract',
				...defaultEdgeOptions
			},
			{
				id: 'ampere-raw-bronze',
				source: 'ampere-raw',
				target: 'ampere-bronze',
				label: 'Spark + Delta',
				...defaultEdgeOptions
			},
			{
				id: 'ampere-bronze-silver',
				source: 'ampere-bronze',
				target: 'ampere-silver',
				label: 'DuckDB + dbt',
				...defaultEdgeOptions
			},
			{
				id: 'ampere-silver-gold',
				source: 'ampere-silver',
				target: 'ampere-gold',
				label: 'DuckDB + dbt',
				...defaultEdgeOptions
			},
			{
				id: 'ampere-gold-serving',
				source: 'ampere-gold',
				target: 'ampere-cache',
				label: 'Caching via Polars job',
				...defaultEdgeOptions
			},
			{
				id: 'ampere-cache-read',
				source: 'ampere-cache',
				target: 'ampere-streamlit',
				label: 'Cache read',
				...defaultEdgeOptions
			}
		]
	},
	{
		id: 'bohr',
		name: 'Bohr',
		description:
			'Infrastructure project: home lab Kubernetes services, KVM/libvirt host, Azure Key Vault, GitHub registry, and Hetzner-hosted Curie runtime are documented as an interactive topology.',
		nodes: [
			{
				id: 'bohr-home-group',
				type: 'group',
				position: { x: 0, y: 0 },
				data: { label: 'Home Lab', toggleDetail: true },
				style: groupStyle(600, 220),
				zIndex: 0
			},
			{
				id: 'bohr-hetzner-group',
				type: 'group',
				position: { x: 750, y: 0 },
				data: { label: 'Public Cloud / Hetzner' },
				style: groupStyle(500, 160),
				zIndex: 0
			},
			{
				id: 'bohr-git',
				data: { label: 'GitHub + GHCR' },
				position: { x: 480, y: 250 },
				sourcePosition: Position.Right,
				targetPosition: Position.Top,
				zIndex: 20
			},
			{
				id: 'bohr-keyvault',
				type: 'output',
				data: { label: 'Azure Key Vault\nSOPS KMS' },
				position: { x: 270, y: 250 },
				targetPosition: Position.Top,
				zIndex: 20
			},
			{
				id: 'bohr-kvm',
				data: { label: 'KVM / libvirt Host\nUbuntu VM fleet' },
				position: { x: 100, y: 95 },
				sourcePosition: Position.Top,
				targetPosition: Position.Top,
				parentId: 'bohr-home-group',
				zIndex: 20
			},
			{
				id: 'bohr-home',
				data: {
					label: 'Internal Kubernetes Cluster',
					handles: {
						sources: [
							{ id: 'to-kv', position: Position.Bottom },
							{ id: 'to-scr', position: Position.Bottom },
							{ id: 'from-home-runtime', position: Position.Bottom }
						],
						targets: [{ id: 'from-kvm', position: Position.Top }]
					}
				},
				position: { x: 375, y: 95 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'bohr-home-group',
				zIndex: 20
			},
			{
				id: 'bohr-hetzner',
				data: { label: 'Hetzner Curie Server\nUbuntu VM', scrollTarget: '#curie' },
				position: { x: 315, y: 72 },
				sourcePosition: Position.Left,
				targetPosition: Position.Bottom,
				parentId: 'bohr-hetzner-group',
				zIndex: 20
			},
			{
				id: 'bohr-curie-runtime',
				type: 'output',
				data: {
					label: 'Curie Docker Runtime\nCompose services',
					handles: {
						targets: [
							{ id: 'from-hetzner', position: Position.Right },
							{ id: 'from-home-runtime', position: Position.Bottom }
						]
					}
				},
				position: { x: 70, y: 72 },
				parentId: 'bohr-hetzner-group',
				zIndex: 20
			}
		],
		edges: [
			{
				id: 'bohr-kvm-home',
				source: 'bohr-kvm',
				target: 'bohr-home',
				targetHandle: 'from-kvm',
				label: 'hosts VMs',
				...defaultEdgeOptions
			},
			{
				id: 'bohr-git-home',
				source: 'bohr-home',
				target: 'bohr-git',
				sourceHandle: 'to-scr',
				label: 'pulls images',
				...defaultEdgeOptions
			},
			{
				id: 'bohr-keyvault-home',
				source: 'bohr-home',
				target: 'bohr-keyvault',
				sourceHandle: 'to-kv',
				label: 'SOPS / ESO',
				...defaultEdgeOptions
			},
			{
				id: 'bohr-git-hetzner',
				source: 'bohr-git',
				target: 'bohr-hetzner',
				label: 'GitHub Actions deploy',
				...defaultEdgeOptions
			},
			{
				id: 'bohr-home-runtime',
				source: 'bohr-home',
				target: 'bohr-curie-runtime',
				targetHandle: 'from-home-runtime',
				label: 'UC / MinIO access',
				...defaultEdgeOptions
			},
			{
				id: 'bohr-hetzner-runtime',
				source: 'bohr-hetzner',
				target: 'bohr-curie-runtime',
				targetHandle: 'from-hetzner',
				label: 'runs containers',
				...defaultEdgeOptions
			}
		],
		detailNodes: [
			{
				id: 'detail-home-group',
				type: 'group',
				position: { x: 80, y: 140 },
				data: { label: 'Home Lab' },
				style: groupStyle(1320, 680),
				targetPosition: Position.Top,
				zIndex: 0
			},
			{
				id: 'detail-cluster-group',
				type: 'group',
				position: { x: 170, y: 50 },
				data: { label: 'Internal Kubernetes Cluster' },
				style: groupStyle(1090, 580),
				parentId: 'detail-home-group',
				zIndex: 0
			},
			{
				id: 'cluster-helmfile',
				type: 'input',
				data: { label: 'Terraform + Helmfile', secondaryLabel: 'Deployment tools' },
				position: { x: 677.5, y: 25 },
				sourcePosition: Position.Bottom,
				zIndex: 20
			},
			{
				id: 'cluster-kvm',
				data: {
					label: 'KVM / libvirt Host',
					secondaryLabel: 'Ubuntu + libvirt',
					disableHandles: true
				},
				position: { x: 35, y: 300 },
				parentId: 'detail-home-group',
				zIndex: 20
			},
			{
				id: 'cluster-cert-manager',
				data: { label: 'cert-manager', secondaryLabel: 'Controller' },
				position: { x: 140, y: 90 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-external-secrets',
				data: { label: 'External Secrets Operator', secondaryLabel: 'Controller' },
				position: { x: 340, y: 90 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-local-path',
				data: { label: 'local-path-provisioner', secondaryLabel: 'StorageClass' },
				position: { x: 540, y: 90 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-cilium',
				data: { label: 'Cilium', secondaryLabel: 'CNI' },
				position: { x: 740, y: 90 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-spark-connect',
				data: {
					label: 'Spark Connect',
					secondaryLabel: 'Service',
					handles: {
						targets: [{ id: 'from-gateway-api', position: Position.Right }]
					}
				},
				position: { x: 20, y: 220 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-gateway-api',
				data: {
					label: 'gateway_api',
					secondaryLabel: 'Routing',
					handles: {
						sources: [
							{ id: 'to-grafana', position: Position.Right },
							{ id: 'to-airflow', position: Position.Bottom },
							{ id: 'to-minio', position: Position.Bottom },
							{ id: 'to-spark-connect', position: Position.Left },
							{ id: 'to-uc-ui', position: Position.Bottom },
							{ id: 'to-uc-server', position: Position.Left },
							{ id: 'to-postgres', position: Position.Bottom }
						],
						targets: [{ id: 'from-cluster-services', position: Position.Top }]
					}
				},
				position: { x: 240, y: 220 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-grafana',
				data: {
					label: 'Grafana',
					secondaryLabel: 'Dashboards',
					handles: {
						sources: [{ id: 'to-prometheus', position: Position.Right }],
						targets: [{ id: 'from-gateway-api', position: Position.Left }]
					}
				},
				position: { x: 440, y: 220 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-prometheus',
				data: {
					label: 'Prometheus',
					secondaryLabel: 'Metrics',
					handles: {
						sources: [{ id: 'to-kube-control', position: Position.Bottom }],
						targets: [{ id: 'from-grafana', position: Position.Left }]
					}
				},
				position: { x: 640, y: 220 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-keda',
				data: { label: 'KEDA', secondaryLabel: 'Autoscaler' },
				position: { x: 840, y: 220 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-airflow',
				data: {
					label: 'Airflow',
					secondaryLabel: 'Workflow engine',
					handles: {
						sources: [
							{ id: 'to-spark', position: Position.Right },
							{ id: 'to-postgres', position: Position.Left },
							{ id: 'to-minio', position: Position.Bottom }
						],
						targets: [
							{ id: 'from-gateway-api', position: Position.Top },
							{ id: 'from-rbac', position: Position.Top },
							{ id: 'from-keda', position: Position.Top }
						]
					}
				},
				position: { x: 640, y: 350 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-postgres',
				data: {
					label: 'PostgreSQL',
					secondaryLabel: 'Meta DB',
					handles: {
						targets: [
							{ id: 'from-gateway-api', position: Position.Left },
							{ id: 'from-airflow', position: Position.Right }
						]
					}
				},
				position: { x: 340, y: 350 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-spark',
				data: {
					label: 'Spark Operator',
					secondaryLabel: 'Controller',
					handles: {
						sources: [
							{ id: 'to-postgres', position: Position.Bottom },
							{ id: 'to-minio', position: Position.Bottom },
							{ id: 'to-ivy-cache', position: Position.Bottom }
						],
						targets: [{ id: 'from-airflow', position: Position.Left }]
					}
				},
				position: { x: 880, y: 350 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-unity-catalog-server',
				data: {
					label: 'Unity Catalog OSS Server',
					secondaryLabel: 'Metadata API',
					handles: {
						sources: [{ id: 'to-minio', position: Position.Bottom }],
						targets: [{ id: 'from-gateway-api', position: Position.Right }]
					}
				},
				position: { x: 20, y: 350 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-minio',
				data: {
					label: 'MinIO',
					secondaryLabel: 'Raw + Delta Lake',
					handles: {
						targets: [
							{ id: 'from-airflow', position: Position.Right },
							{ id: 'from-uc', position: Position.Left },
							{ id: 'from-gateway-api', position: Position.Top }
						]
					}
				},
				position: { x: 140, y: 480 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			},
			{
				id: 'cluster-ivy-cache',
				data: { label: 'Ivy cache', secondaryLabel: 'PVC' },
				position: { x: 880, y: 480 },
				sourcePosition: Position.Bottom,
				targetPosition: Position.Top,
				parentId: 'detail-cluster-group',
				zIndex: 20
			}
		],
		detailEdges: [
			{
				id: 'cluster-external-secrets-resources-operator',
				source: 'cluster-external-secrets-resources',
				target: 'cluster-external-secrets',
				label: 'defines stores',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-cert-manager-gateway-api',
				source: 'cluster-cert-manager',
				target: 'cluster-gateway-api',
				targetHandle: 'from-cluster-services',
				label: 'issues TLS',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-airflow',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-airflow',
				target: 'cluster-airflow',
				targetHandle: 'from-gateway-api',
				label: 'routes UI/API',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-minio',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-minio',
				target: 'cluster-minio',
				targetHandle: 'from-gateway-api',
				label: 'routes S3',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-spark-connect',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-spark-connect',
				target: 'cluster-spark-connect',
				targetHandle: 'from-gateway-api',
				label: 'routes gRPC',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-uc-ui',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-uc-ui',
				target: 'cluster-unity-catalog-ui',
				label: 'routes UI',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-uc-server',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-uc-server',
				target: 'cluster-unity-catalog-server',
				targetHandle: 'from-gateway-api',
				label: 'routes API',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-postgres',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-postgres',
				target: 'cluster-postgres',
				targetHandle: 'from-gateway-api',
				label: 'routes TCP',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-gateway-api-grafana',
				source: 'cluster-gateway-api',
				sourceHandle: 'to-grafana',
				target: 'cluster-grafana',
				targetHandle: 'from-gateway-api',
				label: 'routes UI',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-airflow-postgres',
				source: 'cluster-airflow',
				sourceHandle: 'to-postgres',
				target: 'cluster-postgres',
				targetHandle: 'from-airflow',
				label: 'metadata',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-airflow-minio',
				source: 'cluster-airflow',
				sourceHandle: 'to-minio',
				target: 'cluster-minio',
				targetHandle: 'from-airflow',
				label: 'S3 data',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-airflow-spark',
				source: 'cluster-airflow',
				sourceHandle: 'to-spark',
				target: 'cluster-spark',
				targetHandle: 'from-airflow',
				label: 'submits jobs',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-spark-ivy-cache',
				source: 'cluster-spark',
				sourceHandle: 'to-ivy-cache',
				target: 'cluster-ivy-cache',
				label: 'JAR cache',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-uc-minio',
				source: 'cluster-unity-catalog-server',
				sourceHandle: 'to-minio',
				target: 'cluster-minio',
				targetHandle: 'from-uc',
				label: 'catalog government',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-prometheus-kube-control',
				source: 'cluster-prometheus',
				sourceHandle: 'to-kube-control',
				target: 'cluster-kube-control',
				label: 'scrapes metrics',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-grafana-prometheus',
				source: 'cluster-grafana',
				sourceHandle: 'to-prometheus',
				target: 'cluster-prometheus',
				targetHandle: 'from-grafana',
				label: 'queries',
				...defaultEdgeOptions
			},
			{
				id: 'cluster-keda-airflow',
				source: 'cluster-keda',
				target: 'cluster-airflow',
				targetHandle: 'from-keda',
				label: 'scales workers',
				...defaultEdgeOptions
			}
		]
	},
	{
		id: 'curie',
		name: 'Curie',
		description:
			'Full-stack reporting project: FastAPI, PostgreSQL, Polars cache refresh workers, SvelteKit frontend, Streamlit report apps, and GitHub Actions deployment to Hetzner.',
		nodes: [
			{
				id: 'curie-user',
				type: 'input',
				data: { label: 'Website user' },
				position: { x: 0, y: 150 },
				sourcePosition: Position.Right
			},
			{
				id: 'curie-web',
				data: {
					label: 'SvelteKit frontend',
					secondaryLabel: 'Main site + Streamlit',
					handles: {
						sources: [
							{ id: 'to-api', position: Position.Right },
							{ id: 'to-cache-storage-web', position: Position.Bottom }
						],
						targets: [{ id: 'from-user', position: Position.Left }]
					}
				},
				position: { x: 320, y: 150 },
				sourcePosition: Position.Right,
				targetPosition: Position.Left
			},
			{
				id: 'curie-ampere-pipeline',
				type: 'input',
				data: { label: 'Ampere Pipeline', secondaryLabel: 'On completion triggers cache refresh' },
				position: { x: 650, y: 0 },
				sourcePosition: Position.Bottom,
				zIndex: 20
			},
			{
				id: 'curie-api',
				data: {
					label: 'FastAPI',
					secondaryLabel: 'Auth, reports, cache API',
					handles: {
						sources: [
							{ id: 'to-postgres', position: Position.Right },
							{ id: 'to-cache-refresh', position: Position.Right }
						],
						targets: [
							{ id: 'from-web', position: Position.Left },
							{ id: 'from-ampere-pipeline', position: Position.Top }
						]
					}
				},
				position: { x: 650, y: 150 },
				sourcePosition: Position.Right,
				targetPosition: Position.Left
			},
			{
				id: 'curie-postgres',
				data: { label: 'PostgreSQL', secondaryLabel: 'Users, roles, reports' },
				position: { x: 1000, y: 0 },
				targetPosition: Position.Left
			},
			{
				id: 'curie-cache',
				data: {
					label: 'Cache refresh worker',
					secondaryLabel: 'Polars + Delta reads',
					handles: {
						sources: [{ id: 'to-cache-storage', position: Position.Left }],
						targets: [{ id: 'from-api', position: Position.Right }]
					}
				},
				position: { x: 1000, y: 300 },
				sourcePosition: Position.Left,
				targetPosition: Position.Bottom
			},
			{
				id: 'curie-cache-storage',
				data: {
					label: 'Cache storage',
					secondaryLabel: 'Parquet files',
					handles: {
						sources: [],
						targets: [
							{ id: 'from-cache-refresh', position: Position.Right },
							{ id: 'from-web', position: Position.Left }
						]
					}
				},
				position: { x: 650, y: 300 },
				zIndex: 20
			}
		],
		edges: [
			{
				id: 'curie-user-web',
				source: 'curie-user',
				target: 'curie-web',
				targetHandle: 'from-user',
				label: 'browser',
				...defaultEdgeOptions
			},
			{
				id: 'curie-web-api',
				source: 'curie-web',
				sourceHandle: 'to-api',
				target: 'curie-api',
				targetHandle: 'from-web',
				label: 'HTTP + cookies',
				...defaultEdgeOptions
			},
			{
				id: 'curie-api-postgres',
				source: 'curie-api',
				sourceHandle: 'to-postgres',
				target: 'curie-postgres',
				label: 'SQLAlchemy',
				...defaultEdgeOptions
			},
			{
				id: 'curie-ampere-pipeline-api',
				source: 'curie-ampere-pipeline',
				target: 'curie-api',
				targetHandle: 'from-ampere-pipeline',
				label: 'HTTP request',
				...defaultEdgeOptions
			},
			{
				id: 'curie-api-cache',
				source: 'curie-api',
				sourceHandle: 'to-cache-refresh',
				target: 'curie-cache',
				targetHandle: 'from-api',
				label: 'Trigger Docker job',
				...defaultEdgeOptions
			},
			{
				id: 'curie-cache-storage',
				source: 'curie-cache',
				sourceHandle: 'to-cache-storage',
				target: 'curie-cache-storage',
				targetHandle: 'from-cache-refresh',
				label: 'writes files',
				...defaultEdgeOptions
			},
			{
				id: 'curie-cache-storage-web',
				source: 'curie-web',
				sourceHandle: 'to-cache-storage-web',
				target: 'curie-cache-storage',
				targetHandle: 'from-web',
				label: 'reads cache',
				...defaultEdgeOptions
			}
		]
	}
];
