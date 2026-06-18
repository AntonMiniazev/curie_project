import type { components } from '@curie/api-client';

import { apiFetch } from './client';

export type ReportItem = components['schemas']['ReportItem'];
export type ReportsResponse = components['schemas']['ReportsResponse'];

export function getReports(): Promise<ReportsResponse> {
	return apiFetch<ReportsResponse>('/api/reports');
}
