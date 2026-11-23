// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

// Dev-only demo of the quiz editor with fake data and a mocked API (no login).
import { dev } from '$app/environment';
import { error } from '@sveltejs/kit';

export const ssr = false;
export const prerender = false;

export const load = () => {
	if (!dev) {
		error(404);
	}
	return {};
};
