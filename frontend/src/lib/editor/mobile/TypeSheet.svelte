<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Phone type picker: two columns of question types, plus a content slide row. -->
<script lang="ts">
	import Sheet from './Sheet.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import TypePreview from '$lib/editor/TypePreview.svelte';
	import { QUESTION_CHOICES, type QuestionChoice } from '$lib/editor/editor_meta';

	interface Props {
		kicker: string;
		/** key of the type the question has now (change mode) */
		current?: string | null;
		/** offer the content slide row */
		allow_slide?: boolean;
		onpick: (c: QuestionChoice) => void;
		onslide?: () => void;
		onclose: () => void;
	}

	let { kicker, current = null, allow_slide = true, onpick, onslide, onclose }: Props = $props();

	// phone order: the quick quiz types first
	const ORDER = ['abcd', 'truefalse', 'check', 'poll', 'cloud', 'text', 'order', 'range'];
	const choices = ORDER.map((k) => QUESTION_CHOICES.find((c) => c.key === k)).filter(
		(c): c is QuestionChoice => Boolean(c)
	);
</script>

<Sheet {kicker} title="Question type" {onclose}>
	<div class="grid grid-cols-2 gap-2.5">
		{#each choices as c (c.key)}
			<button
				type="button"
				class="tcard"
				class:tcard-on={current === c.key}
				aria-current={current === c.key ? 'true' : undefined}
				onclick={() => onpick(c)}
			>
				<span class="art" aria-hidden="true"><TypePreview kind={c.preview} /></span>
				<span class="name">{c.name}</span>
				<span class="blurb">{c.blurb}</span>
			</button>
		{/each}
	</div>
	{#if allow_slide && onslide}
		<button type="button" class="slide-row" onclick={onslide}>
			<EdIcon name="slide" size={20} />
			<span class="flex-1 text-left">Content slide instead</span>
			<EdIcon name="right" size={20} />
		</button>
	{/if}
</Sheet>

<style>
	.tcard {
		display: flex;
		flex-direction: column;
		min-width: 0;
		padding: 8px 8px 12px;
		border-radius: 20px;
		background: var(--fill-glass);
		text-align: left;
	}
	.tcard:active {
		background: var(--fill-glass-mid);
	}
	.tcard-on {
		box-shadow: inset 0 0 0 2px var(--accent-sky);
	}
	.tcard:focus-visible,
	.slide-row:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.art {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 64px;
		padding: 8px;
		border-radius: 14px;
		background: var(--fill-deep);
		overflow: hidden;
	}
	.name {
		display: block;
		margin: 10px 4px 2px;
		font-size: 15px;
		font-weight: 900;
		line-height: 1.15;
		letter-spacing: 0.5px;
		text-transform: uppercase;
	}
	.blurb {
		display: block;
		margin: 0 4px;
		font-size: 13px;
		line-height: 1.25;
		color: var(--ink-muted);
	}
	.slide-row {
		display: flex;
		align-items: center;
		gap: 12px;
		width: 100%;
		min-height: 52px;
		margin-top: 10px;
		padding: 0 18px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		font-size: 15px;
		font-weight: 700;
	}
</style>
