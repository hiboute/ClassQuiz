// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import type { Handle } from '@sveltejs/kit';
import { dev } from '$app/environment';
import * as jose from 'jose';

/** @type {import('@sveltejs/kit').Handle} */
export const handle: Handle = async ({ event, resolve }) => {
	// /__demo/** are dev-only harnesses with fake data. Their pages render
	// client-side only (ssr = false), so the layout's 404 alone would still
	// answer HTTP 200 with an app shell: refuse them here in production.
	if (!dev && (event.url.pathname === '/__demo' || event.url.pathname.startsWith('/__demo/'))) {
		return new Response('Not found', { status: 404, headers: { 'Content-Type': 'text/plain' } });
	}
	const access_token = event.cookies.get('access_token');
	if (!access_token) {
		event.locals.email = null;
		return resolve(event);
	}
	const jwt = jose.decodeJwt(access_token.replace('Bearer ', ''));
	if (!jwt) {
		event.locals.email = null;
		return resolve(event);
	}
	// if token expires, do a request to get a new one and set the response-cookies on the response
	if (Date.now() >= jwt.exp * 1000) {
		const res = await fetch(`${process.env.API_URL}/api/v1/users/check`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Cookie: event.request.headers.get('cookie') || ''
			}
		});
		if (res.ok) {
			event.locals.email = await res.text();
			const resp = await resolve(event);
			try {
				resp.headers.set('Set-Cookie', res.headers.get('set-cookie'));
			} catch {
				/* empty */
			}
			return resp;
		}
	}
	event.locals.email = jwt.sub;
	return resolve(event);
};
