import type { Position } from '@xyflow/svelte';

export type FlowHandleConfig = {
	id?: string;
	position: Position;
};

export type FlowNodeData = {
	disableHandles?: boolean;
	handles?: {
		sources?: FlowHandleConfig[];
		targets?: FlowHandleConfig[];
	};
	label: string;
	labelClass?: string;
	secondaryLabel?: string;
	secondaryLabelClass?: string;
	scrollTarget?: string;
	toggleDetail?: boolean;
};

export type FlowEdgeLabelStyle = {
	backgroundColor?: string;
	borderColor?: string;
	borderStyle?: string;
	borderWidth?: string;
	fontSize?: string;
	textColor?: string;
};

export type FlowEdgeData = {
	labelClass?: string;
	labelVisual?: FlowEdgeLabelStyle;
};
