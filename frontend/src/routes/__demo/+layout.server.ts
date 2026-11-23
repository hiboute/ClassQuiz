// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

// Every /__demo/** page is a dev-only harness with fake data. A production
// build answers 404: hooks.server.ts refuses the URLs with a real HTTP 404,
// and this load errors too for client-side navigation (it runs on the server
// through __data.json, also for the ssr = false pages).
import { dev } from '$app/environment';
import { error } from '@sveltejs/kit';

export const prerender = false;

export const load = () => {
	if (!dev) error(404, 'Not found');
	return {};
};
