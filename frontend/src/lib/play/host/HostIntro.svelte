<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- After Start, before the first question: the quiz title and the room. -->
<script lang="ts">
	import { fitText } from './fit';
	import { plain } from './worlds';

	interface Props {
		title: string;
		description?: string;
		questionCount: number;
		playerCount: number;
	}

	let { title, description = '', questionCount, playerCount }: Props = $props();
	const t = $derived(plain(title));
	const d = $derived(plain(description));
</script>

<div class="in">
	<span class="h-label in-label">{playerCount} {playerCount === 1 ? 'player' : 'players'}, {questionCount}
		{questionCount === 1 ? 'question' : 'questions'}</span>
	<h1 class="in-title bt-text-display" use:fitText={{ max: 120, min: 56, lines: 2, key: t }}>{t}</h1>
	{#if d}<p class="in-desc">{d}</p>{/if}
	<p class="in-ready">Phones ready. First question coming up.</p>
</div>

<style>
	.in {
		position: absolute;
		inset: 0 160px 120px;
		z-index: 3;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
	}
	.in-label {
		font-size: 28px;
		font-weight: 700;
	}
	.in-title {
		margin: 30px 0 0;
		width: 1600px;
		font-size: 120px;
		font-weight: 900;
		line-height: 1.08;
		text-transform: uppercase;
		padding-bottom: 6px;
	}
	.in-desc {
		margin: 26px 0 0;
		max-width: 1300px;
		font-size: 32px;
		color: var(--ink-muted);
	}
	.in-ready {
		margin: 60px 0 0;
		font-size: 30px;
		font-weight: 400;
		text-transform: uppercase;
	}
</style>
