<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	One quiz on the phone dashboard: colour swatch, title and facts (tap to
	edit), a problem, Ready or Draft chip, when it was edited, and Play. The
	other actions sit in a bottom sheet behind the more button.
-->
<script lang="ts">
	import { DateTime } from 'luxon';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { questionWorld } from '$lib/brand/answers';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import Sheet from '$lib/editor/mobile/Sheet.svelte';
	import { plainText, questionIssue, quizMinutes } from '$lib/editor/editor_meta';
	import type { Question } from '$lib/quiz_types';

	interface Props {
		item: {
			id: string;
			type: 'quiz' | 'quiztivity';
			title: string;
			public?: boolean;
			questions?: unknown[];
			pages?: unknown[];
			plays?: number;
			updated_at?: string;
		};
		index: number;
		onstart: () => void;
		onanalytics: () => void;
		ondownload: () => void;
		ondelete: () => void;
	}

	let { item, index, onstart, onanalytics, ondownload, ondelete }: Props = $props();

	let menu_open = $state(false);

	const is_quiz = $derived(item.type === 'quiz');
	const questions = $derived((is_quiz ? (item.questions ?? []) : []) as Question[]);
	const count = $derived(is_quiz ? questions.length : (item.pages?.length ?? 0));
	const title = $derived(plainText(item.title) || 'Untitled quiz');
	const problems = $derived(questions.filter((q) => questionIssue(q)).length);
	const edit_href = $derived(
		is_quiz ? `/edit?quiz_id=${item.id}` : `/quiztivity/edit?id=${item.id}`
	);
	const facts = $derived.by(() => {
		if (!is_quiz) return [`${count} ${count === 1 ? 'page' : 'pages'}`, 'Quiztivity'];
		if (count === 0) return ['Draft, no questions yet'];
		const out = [`${count} ${count === 1 ? 'question' : 'questions'}`];
		out.push(`about ${quizMinutes(questions)} min`);
		if (item.plays) out.push(`played ${item.plays === 1 ? 'once' : `${item.plays} times`}`);
		else out.push(item.public ? 'Public' : 'Private');
		return out;
	});
	const edited = $derived.by(() => {
		if (!item.updated_at) return '';
		const d = DateTime.fromISO(item.updated_at);
		return d.isValid ? `Edited ${d.toRelative({ style: 'short' })}` : '';
	});
	const action = (fn: () => void) => () => {
		menu_open = false;
		fn();
	};
</script>

<article class="card">
	<div class="flex items-start gap-3">
		<a href={edit_href} class="main" aria-label="Edit {title}">
			<span class="sw" data-world={questionWorld(index)} aria-hidden="true">
				{#each [0, 1, 2, 3] as k}
					<span><ShapeMark index={k} size={13} color="rgba(255,255,255,.88)" /></span>
				{/each}
			</span>
			<span class="min-w-0 flex-1">
				<span class="title">{title}</span>
				<span class="facts">{facts.join(' · ')}</span>
			</span>
		</a>
		<button
			type="button"
			class="more"
			aria-label="More actions for {title}"
			aria-haspopup="dialog"
			onclick={() => (menu_open = true)}
		>
			<EdIcon name="more" size={22} stroke={3.2} />
		</button>
	</div>
	<div class="foot">
		{#if is_quiz && count === 0}
			<span class="chip">Draft</span>
		{:else if problems > 0}
			<span class="chip chip-warn"><EdIcon name="warn" size={14} />{problems} to fix</span>
		{:else if is_quiz}
			<span class="chip chip-ok"><EdIcon name="check" size={14} stroke={3} />Ready</span>
		{/if}
		<span class="min-w-0 flex-1 truncate text-[13px] text-ink-muted">{edited}</span>
		{#if is_quiz && count > 0}
			<button type="button" class="bt-btn-ghost play" onclick={onstart}>
				<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"
					><path d="M7 4.5v15l13-7.5z" /></svg
				>
				Play
			</button>
		{:else if !is_quiz}
			<a href="/quiztivity/play?id={item.id}" class="bt-btn-ghost play">Play</a>
		{:else}
			<a href={edit_href} class="bt-btn-ghost play">Edit</a>
		{/if}
	</div>
</article>

{#if menu_open}
	<Sheet kicker={is_quiz ? 'Quiz' : 'Quiztivity'} title={title} onclose={() => (menu_open = false)}>
		<div class="flex flex-col gap-2">
			<a href={edit_href} class="act"><EdIcon name="pencil" size={20} /> Edit</a>
			{#if is_quiz}
				<a href="/results?quiz={item.id}" class="act"><EdIcon name="clock" size={20} /> Results</a>
				{#if item.public}
					<a href="/view/{item.id}" class="act"><EdIcon name="globe" size={20} /> Public page</a>
				{/if}
				<button type="button" class="act" onclick={action(onanalytics)}
					><EdIcon name="search" size={20} /> Views and plays</button
				>
				<button type="button" class="act" onclick={action(ondownload)}
					><EdIcon name="save" size={20} /> Download</button
				>
			{/if}
			<button type="button" class="act act-danger" onclick={action(ondelete)}
				><EdIcon name="trash" size={20} /> Delete</button
			>
		</div>
	</Sheet>
{/if}

<style>
	.card {
		padding: 14px 6px 14px 14px;
		border-radius: 25px;
		background: var(--fill-glass);
	}
	.main {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		flex: 1;
		min-width: 0;
		min-height: 56px;
		border-radius: 16px;
	}
	.sw {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 4px;
		flex: none;
		width: 56px;
		height: 56px;
		padding: 10px;
		border-radius: 16px;
		background: linear-gradient(135deg, var(--ground-glow), var(--ground-mid) 60%, var(--ground));
	}
	.sw > span {
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.title {
		display: -webkit-box;
		overflow: hidden;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		font-size: 18px;
		font-weight: 700;
		line-height: 1.2;
	}
	.facts {
		display: block;
		margin-top: 4px;
		font-size: 14px;
		color: var(--ink-muted);
	}
	.more {
		display: grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 999px;
	}
	.foot {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-top: 12px;
		padding-right: 8px;
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		flex: none;
		height: 30px;
		padding: 0 12px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		font-size: 13px;
		font-weight: 700;
	}
	.chip-warn {
		background: rgba(215, 131, 255, 0.22);
		color: var(--accent-orchid-tint);
	}
	.chip-ok {
		background: rgba(39, 190, 130, 0.2);
		color: var(--accent-green-tint);
	}
	.play {
		flex: none;
		min-height: 44px;
		padding: 0 18px;
		font-size: 14px;
		letter-spacing: 2px;
	}
	.main:focus-visible,
	.more:focus-visible,
	.act:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.act {
		display: flex;
		align-items: center;
		gap: 14px;
		min-height: 56px;
		padding: 0 18px;
		border-radius: 18px;
		background: var(--fill-glass);
		font-size: 16px;
		font-weight: 700;
		text-align: left;
	}
	.act-danger {
		color: #ffb3d9;
	}
</style>
