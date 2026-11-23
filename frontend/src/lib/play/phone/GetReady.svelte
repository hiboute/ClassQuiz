<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Full-screen "get ready" before a question: question number, title and a
	3-2-1 count, in that question's colour world.
-->
<script lang="ts">
	import { onDestroy } from 'svelte';
	import PhoneShell from './PhoneShell.svelte';
	import { plainText, questionWorld, type GetReadyData } from './phone';

	interface Props {
		data: GetReadyData;
		question_count?: number;
		/** Date.now() when the event arrived */
		received_at?: number;
	}

	let { data, question_count, received_at = Date.now() }: Props = $props();

	let now = $state(Date.now());
	const tick = setInterval(() => (now = Date.now()), 100);
	onDestroy(() => clearInterval(tick));

	const total = $derived(Math.max(0, Number(data.seconds) || 0));
	const left = $derived(Math.max(0, Math.ceil(total - (now - received_at) / 1000)));
	const world = $derived(questionWorld(data.question_index));
	const qc = $derived(question_count ?? data.question_count);
	const title = $derived(plainText(data.title));
	const is_slide = $derived(String(data.type).toUpperCase() === 'SLIDE');
	const double = $derived(data.points === 'double');
	const no_points = $derived(data.points === 'none');
	const type_label = $derived.by(() => {
		switch (String(data.type).toUpperCase()) {
			case 'CHECK':
				return 'Pick every right answer';
			case 'TEXT':
				return 'Type your answer';
			case 'RANGE':
				return 'Slide to your answer';
			case 'ORDER':
				return 'Put them in order';
			case 'VOTING':
				return 'Vote';
			case 'WORD_CLOUD':
				return 'Word cloud';
			case 'SLIDE':
				return 'Look at the screen';
			default:
				return 'Pick one answer';
		}
	});
</script>

<PhoneShell {world} state="get-ready">
	<div class="gr-top">
		<span class="bt-eyebrow">
			{is_slide ? 'Next up' : 'Question'}
		</span>
		{#if !is_slide}
			<b class="gr-index bt-num"
				>{data.question_index + 1}{#if qc}<span class="gr-of">&nbsp;/ {qc}</span>{/if}</b
			>
		{/if}
	</div>

	<div class="gr-count" aria-live="assertive" data-testid="get-ready">
		{#key left}
			<span class="gr-num bt-num bt-text-aurora">{left > 0 ? left : 'Go'}</span>
		{/key}
	</div>

	<div class="gr-bottom">
		<span class="bt-kicker gr-kicker">Get ready</span>
		{#if title}
			<p class="gr-title">{title}</p>
		{/if}
		<div class="gr-tags">
			<span class="gr-tag">{type_label}</span>
			{#if double}
				<span class="gr-tag gr-tag-hot">Double points</span>
			{:else if no_points && !is_slide}
				<span class="gr-tag">No points</span>
			{/if}
		</div>
	</div>
</PhoneShell>

<style>
	.gr-top .bt-eyebrow {
		font-size: 15px;
	}
	.gr-index {
		display: block;
		margin-top: 6px;
		font-size: 44px;
		line-height: 0.9;
	}
	.gr-of {
		font-weight: 400;
		font-size: 26px;
	}
	.gr-count {
		flex: 1 1 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 240px;
	}
	.gr-num {
		display: block;
		font-size: 220px;
		line-height: 1;
		padding: 0 8px;
		animation: gr-pop 900ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
	}
	@keyframes gr-pop {
		from {
			transform: scale(0.6);
			opacity: 0;
		}
		30% {
			transform: scale(1.04);
			opacity: 1;
		}
		to {
			transform: scale(1);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.gr-num {
			animation: none;
		}
	}
	.gr-kicker {
		font-size: 20px;
	}
	.gr-title {
		margin: 8px 0 0;
		font-size: 26px;
		font-weight: 900;
		line-height: 1.15;
		display: -webkit-box;
		-webkit-line-clamp: 4;
		line-clamp: 4;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.gr-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 18px;
	}
	.gr-tag {
		display: inline-flex;
		align-items: center;
		min-height: 34px;
		padding: 0 16px;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		font-size: 13px;
		letter-spacing: 2px;
		text-transform: uppercase;
	}
	.gr-tag-hot {
		background: var(--fill-deep);
		color: var(--accent-green-tint);
		font-weight: 700;
	}
</style>
