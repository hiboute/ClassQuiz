<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Solid answer shape. Pass `shape`, or `index` (0..3 = triangle, diamond,
	circle, square). Fills with currentColor unless `color` is set.
-->
<script lang="ts">
	import { answerStyle, type AnswerShape } from './answers';

	interface Props {
		shape?: AnswerShape;
		index?: number;
		size?: number | string;
		color?: string;
		title?: string;
		class?: string;
	}

	let { shape, index = 0, size = '1em', color = 'currentColor', title, class: klass = '' }: Props =
		$props();

	const resolved = $derived<AnswerShape>(shape ?? answerStyle(index).shape);
	const dim = $derived(typeof size === 'number' ? `${size}px` : size);
</script>

<svg
	viewBox="0 0 100 100"
	width={dim}
	height={dim}
	fill={color}
	class={klass}
	style="display:block;flex:none"
	role={title ? 'img' : undefined}
	aria-hidden={title ? undefined : 'true'}
	aria-label={title}
>
	{#if resolved === 'triangle'}
		<path d="M50 8 L94 88 L6 88 Z" />
	{:else if resolved === 'diamond'}
		<path d="M50 2 L98 50 L50 98 L2 50 Z" />
	{:else if resolved === 'circle'}
		<circle cx="50" cy="50" r="44" />
	{:else}
		<rect x="10" y="10" width="80" height="80" />
	{/if}
</svg>
