// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

export interface FitOptions {
	max: number;
	min: number;
	lines: number;
	/** change it when the text changes, so the size is measured again */
	key?: unknown;
	/** check the width only (single-line display numbers with a tight line height) */
	widthOnly?: boolean;
}

/**
 * Shrinks the font size of a block, from `max` down to `min`, until its text
 * fits in `lines` lines and does not overflow sideways.
 */
export function fitText(node: HTMLElement, options: FitOptions) {
	let opts = options;
	let frame = 0;
	const run = () => {
		cancelAnimationFrame(frame);
		frame = requestAnimationFrame(() => {
			let size = opts.max;
			node.style.fontSize = `${size}px`;
			const cs = getComputedStyle(node);
			const ratio = parseFloat(cs.lineHeight) / size || 1.1;
			const padY = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
			const fits = () =>
				(opts.widthOnly ||
					node.scrollHeight - padY <= Math.ceil(ratio * size * opts.lines) + 2) &&
				node.scrollWidth <= node.clientWidth + 1;
			while (!fits() && size > opts.min) {
				size -= 2;
				node.style.fontSize = `${size}px`;
			}
		});
	};
	run();
	document.fonts?.ready.then(run);
	return {
		update(next: FitOptions) {
			opts = next;
			run();
		},
		destroy() {
			cancelAnimationFrame(frame);
		}
	};
}
