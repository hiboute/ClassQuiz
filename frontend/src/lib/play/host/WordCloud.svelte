<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Live word cloud: sizes by count, brand colours, no overlap (spiral layout,
	measured with a canvas). Words glide to their new place as counts change.
-->
<script lang="ts">
	import { scale } from 'svelte/transition';
	import type { WordCount } from './worlds';

	interface Props {
		words: WordCount[];
		width: number;
		height: number;
		max?: number;
	}

	let { words, width, height, max = 60 }: Props = $props();

	const COLORS = [
		'#5db5df',
		'#27be82',
		'#d783ff',
		'#f982fa',
		'#a59fff',
		'#83c8d8',
		'#73e2b6',
		'#e7b5ff',
		'#9ed3ec',
		'#418eed'
	];
	const FONT = "'LOREAL Essentielle', 'Century Gothic', sans-serif";

	interface Placed {
		key: string;
		text: string;
		count: number;
		size: number;
		x: number;
		y: number;
		w: number;
		h: number;
		color: string;
		top: boolean;
	}

	let fontsReady = $state(0);
	$effect(() => {
		document.fonts?.ready.then(() => (fontsReady += 1));
	});

	let ctx: CanvasRenderingContext2D | null = null;
	const measure = (text: string, size: number): number => {
		if (typeof document === 'undefined') return text.length * size * 0.6;
		if (!ctx) ctx = document.createElement('canvas').getContext('2d');
		if (!ctx) return text.length * size * 0.6;
		ctx.font = `900 ${size}px ${FONT}`;
		return ctx.measureText(text.toUpperCase()).width;
	};

	const placed = $derived.by((): Placed[] => {
		void fontsReady;
		const list = [...words]
			.filter((w) => w.text && w.count > 0)
			.sort((a, b) => b.count - a.count || a.text.localeCompare(b.text))
			.slice(0, max);
		if (!list.length) return [];
		const hi = list[0].count;
		const lo = list[list.length - 1].count;
		const maxSize = list.length < 6 ? 150 : list.length < 15 ? 120 : 96;
		const minSize = 26;
		const out: Placed[] = [];
		const gap = 10;
		const cx = width / 2;
		const cy = height / 2;
		const aspect = width / height;
		const hits = (x: number, y: number, w: number, h: number) =>
			x < 0 ||
			y < 0 ||
			x + w > width ||
			y + h > height ||
			out.some(
				(p) =>
					x < p.x + p.w + gap && x + w + gap > p.x && y < p.y + p.h + gap && y + h + gap > p.y
			);
		list.forEach((word, i) => {
			const t = hi === lo ? 1 : Math.sqrt((word.count - lo) / (hi - lo));
			let size = Math.round(minSize + (maxSize - minSize) * t);
			for (let attempt = 0; attempt < 4; attempt++) {
				const w = Math.ceil(measure(word.text, size)) + 4;
				const h = Math.ceil(size * 1.05);
				let done = false;
				for (let step = 0; step < 1800; step++) {
					const a = step * 0.18;
					const r = 3 * a;
					const x = cx + r * Math.cos(a) * Math.sqrt(aspect) - w / 2;
					const y = cy + (r * Math.sin(a)) / Math.sqrt(aspect) - h / 2;
					if (!hits(x, y, w, h)) {
						out.push({
							key: word.text.toLocaleLowerCase(),
							text: word.text,
							count: word.count,
							size,
							x,
							y,
							w,
							h,
							color: COLORS[i % COLORS.length],
							top: i === 0
						});
						done = true;
						break;
					}
				}
				if (done) break;
				size = Math.max(18, Math.round(size * 0.8));
			}
		});
		return out;
	});
</script>

<div class="wc" style="width: {width}px; height: {height}px">
	{#each placed as word (word.key)}
		<span
			class="wc-word"
			style="transform: translate({word.x}px, {word.y}px); font-size: {word.size}px"
			title="{word.text}: {word.count}"
		>
			<span
				class="wc-in"
				class:bt-text-aurora={word.top}
				style="color: {word.top ? 'transparent' : word.color}"
				in:scale={{ start: 0.3, duration: 400 }}>{word.text}</span
			>
		</span>
	{/each}
</div>

<style>
	.wc {
		position: relative;
	}
	.wc-word {
		position: absolute;
		left: 0;
		top: 0;
		font-weight: 900;
		line-height: 1.05;
		text-transform: uppercase;
		white-space: nowrap;
		will-change: transform;
		transition:
			transform 700ms cubic-bezier(0.2, 0.8, 0.2, 1),
			font-size 700ms cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.wc-in {
		display: inline-block;
	}
</style>
