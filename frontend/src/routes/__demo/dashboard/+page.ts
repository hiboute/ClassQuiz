// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

// Dev-only demo of the organiser pages with fake data. 404 in production builds.
import { dev } from '$app/environment';
import { error } from '@sveltejs/kit';

export const ssr = false;
export const prerender = false;

export const load = () => {
	if (!dev) error(404);
	return {};
};
