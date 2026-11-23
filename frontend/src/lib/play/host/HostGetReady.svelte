<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	"Get ready" before each question: index, title and a 3-2-1 count, in the
	question's own world (the stage around it sets the world).
-->
<script lang="ts">
	import { scale } from 'svelte/transition';
	import { fitText } from './fit';
	import { plain, TYPE_LABEL, type GetReadyData } from './worlds';
	import { hostSound } from './sound.svelte';

	interface Props {
		data: GetReadyData;
		total: number;
		/** freeze the count (demo screenshots) */
		frozen?: boolean;
	}

	let { data, total, frozen = false }: Props = $props();

	let left = $state(0);

	$effect(() => {
		const start = Math.max(1, Math.round(data.seconds || 3));
		left = start;
		if (frozen) return;
		hostSound.count();
		const id = setInterval(() => {
			left = Math.max(0, left - 1);
			if (left > 0) hostSound.count();
			else {
				hostSound.count(true);
				clearInterval(id);
			}
		}, 1000);
		return () => clearInterval(id);
	});

	const title = $derived(plain(data.title));
</script>

<div class="gr">
	<div class="gr-top">
		<span class="h-label gr-label">Question {data.question_index + 1} of {total}</span>
		<span class="gr-chips">
			{#if TYPE_LABEL[data.type]}<span class="gr-chip">{TYPE_LABEL[data.type]}</span>{/if}
			{#if data.points === 'double'}<span class="gr-chip gr-chip--double">Double points</span>{/if}
			{#if data.points === 'none'}<span class="gr-chip">No points</span>{/if}
		</span>
	</div>
	<h1 class="gr-title" use:fitText={{ max: 84, min: 44, lines: 3, key: title }}>{title}</h1>
	<div class="gr-count" aria-live="polite">
		{#key left}
			<span class="h-num bt-text-display gr-num" in:scale={{ start: 1.6, duration: 380 }}
				>{left > 0 ? left : 'Go'}</span
			>
		{/key}
	</div>
</div>

<style>
	.gr {
		position: absolute;
		inset: 0;
		z-index: 3;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		padding: 0 160px 80px;
	}
	.gr-top {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 22px;
	}
	.gr-label {
		font-size: 28px;
		font-weight: 700;
	}
	.gr-chips {
		display: flex;
		gap: 12px;
	}
	.gr-chip {
		height: 48px;
		display: inline-flex;
		align-items: center;
		padding: 0 26px;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		font-size: 22px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 3px;
	}
	.gr-chip--double {
		background: linear-gradient(90deg, var(--accent-pink) 0%, var(--accent-orchid) 100%);
		color: var(--ink-dark);
	}
	.gr-title {
		margin: 40px 0 0;
		width: 1500px;
		font-size: 84px;
		font-weight: 900;
		line-height: 1.08;
		text-transform: uppercase;
		overflow-wrap: anywhere;
	}
	.gr-count {
		position: relative;
		margin-top: 56px;
		width: 340px;
		height: 340px;
		border-radius: 50%;
		background: var(--fill-deep);
		display: grid;
		place-items: center;
	}
	.gr-num {
		grid-area: 1 / 1;
		font-size: 220px;
		line-height: 1;
		padding-bottom: 10px;
		text-transform: uppercase;
	}
</style>
