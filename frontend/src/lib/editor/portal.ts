// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

/**
 * Moves an overlay to <body>. Glass panels use backdrop-filter, which makes
 * them the containing block of `position: fixed` children: a modal left
 * inside one would be clipped to the panel instead of covering the page.
 */
export function portal(node: HTMLElement) {
	document.body.appendChild(node);
	return {
		destroy() {
			node.remove();
		}
	};
}
