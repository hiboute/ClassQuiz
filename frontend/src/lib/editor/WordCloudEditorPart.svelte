<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Word cloud question: nothing to set but the question, the time and an
	optional image. Players type a short word (1 to 30 characters) and the big
	screen shows a live cloud. No correct answer and no points.
-->
<script lang="ts">
	import type { EditorData } from '$lib/quiz_types';

	interface Props {
		selected_question: number;
		data: EditorData;
	}

	let { selected_question, data = $bindable() }: Props = $props();

	// a word cloud stores no answers (the server keeps an empty list)
	if (!Array.isArray(data.questions[selected_question].answers)) {
		data.questions[selected_question].answers = [];
	}

	const sample = [
		{ text: 'innovation', size: 44, color: 'var(--accent-sky)' },
		{ text: 'skin', size: 22, color: 'var(--accent-green-tint)' },
		{ text: 'beauty', size: 34, color: 'var(--accent-pink)' },
		{ text: 'AI', size: 28, color: 'var(--ink)' },
		{ text: 'data', size: 18, color: 'var(--accent-lavender)' },
		{ text: 'care', size: 26, color: 'var(--accent-orchid)' },
		{ text: 'future', size: 20, color: 'var(--accent-aqua)' },
		{ text: 'colour', size: 16, color: 'var(--ink-muted)' }
	];
</script>

<span class="bt-eyebrow mb-4 text-[11px] text-ink-muted">Answers</span>
<div class="cloud-preview" aria-hidden="true">
	{#each sample as w}
		<span style="font-size:{w.size}px;color:{w.color}">{w.text}</span>
	{/each}
</div>
<div class="mt-4 grid gap-3 sm:grid-cols-3">
	<div class="fact">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Players</span>
		<span class="block font-bold">Type one short word</span>
		<span class="block text-xs text-ink-muted">1 to 30 characters, on their phone</span>
	</div>
	<div class="fact">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Big screen</span>
		<span class="block font-bold">Shows a live cloud</span>
		<span class="block text-xs text-ink-muted">Popular words grow as they come in</span>
	</div>
	<div class="fact">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Scoring</span>
		<span class="block font-bold">No points</span>
		<span class="block text-xs text-ink-muted">No correct answer, streaks unchanged</span>
	</div>
</div>

<style>
	.cloud-preview {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: center;
		gap: 4px 18px;
		padding: 28px 20px;
		border-radius: 18px;
		background: var(--fill-deep);
		font-weight: 900;
		line-height: 1;
		text-transform: lowercase;
		opacity: 0.9;
	}
	.fact {
		padding: 14px;
		border-radius: 16px;
		background: var(--fill-glass);
	}
</style>
