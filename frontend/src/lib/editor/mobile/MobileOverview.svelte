<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone quiz overview: editable title card, facts, a banner per problem, the
	question list (tap a row to edit it, Reorder to move rows), and a bottom bar
	with the save state and "+ Question".
-->
<script lang="ts">
	import type { EditorData } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import Loading from '$lib/editor/Loading.svelte';
	import SaveState from './SaveState.svelte';
	import ProblemChip from './ProblemChip.svelte';
	import { flip } from 'svelte/animate';
	import { questionWorld } from '$lib/brand/answers';
	import { plainText, pointsOf, questionTypeName, quizMinutes } from '$lib/editor/editor_meta';

	interface Props {
		data: EditorData;
		issues: (string | null)[];
		settings_issue: string | null;
		problem_count: number;
		save_tone: 'bad' | 'ok' | 'busy';
		save_label: string;
		save_hint: string;
		can_save: boolean;
		saving: boolean;
		/** changes when the title was edited elsewhere (settings sheet) */
		title_rev?: number;
		onsave: () => void;
		onopen: (index: number) => void;
		onadd: () => void;
		onsettings: () => void;
		onproblems: () => void;
		onmove: (from: number, to: number) => void;
	}

	let {
		data = $bindable(),
		issues,
		settings_issue,
		problem_count,
		save_tone,
		save_label,
		save_hint,
		can_save,
		saving,
		title_rev = 0,
		onsave,
		onopen,
		onadd,
		onsettings,
		onproblems,
		onmove
	}: Props = $props();

	let reorder = $state(false);
	let title_box: HTMLElement | undefined = $state();

	const question_count = $derived(
		data.questions.filter((q) => q.type !== QuizQuestionType.SLIDE).length
	);
	const minutes = $derived(quizMinutes(data.questions));
	const broken = $derived(issues.filter(Boolean).length);

	// stable keys for the animated list (questions have no id of their own)
	const keys = new WeakMap<object, number>();
	let next_key = 0;
	const keyOf = (q: object): number => {
		if (!keys.has(q)) keys.set(q, next_key++);
		return keys.get(q) as number;
	};

	const focus_title = () => {
		title_box?.querySelector<HTMLElement>('[contenteditable]')?.focus();
	};
</script>

<div class="ov">
	<header class="top">
		<a
			href="/dashboard"
			class="ib"
			aria-label="Back to the dashboard"
			onclick={(e) => {
				if (!saving && !confirm('Leave the editor? Changes since the last save are lost.')) {
					e.preventDefault();
				}
			}}
		>
			<EdIcon name="back" size={22} />
		</a>
		<span class="lbl flex-1 text-center">Quiz</span>
		{#if problem_count > 0}
			<ProblemChip count={problem_count} onclick={onproblems} />
		{/if}
		<button
			type="button"
			class="bt-btn-primary save-btn"
			disabled={!can_save}
			onclick={onsave}
		>
			<EdIcon name="save" size={17} stroke={2.5} />
			{saving ? 'Saving' : 'Save'}
		</button>
		<button type="button" class="ib" aria-label="Quiz settings" onclick={onsettings}>
			<EdIcon name="sliders" size={20} />
		</button>
	</header>

	<div class="scroll">
		<div class="wrap">
			<div class="title-card" bind:this={title_box}>
				<div class="min-w-0 flex-1">
					<span class="lbl lbl-sm">Quiz title</span>
					<div class="q-title relative">
						{#key title_rev}
							{#await import('$lib/inline-editor.svelte')}
								<Loading />
							{:then c}
								<c.default bind:text={data.title} />
							{/await}
						{/key}
						{#if !plainText(data.title)}
							<span class="q-placeholder" aria-hidden="true">Name your quiz</span>
						{/if}
					</div>
				</div>
				<button type="button" class="ib ib-plain" aria-label="Edit the title" onclick={focus_title}>
					<EdIcon name="pencil" size={20} />
				</button>
			</div>

			<div class="facts">
				<span class="fact"
					><EdIcon name={data.public ? 'globe' : 'lock'} size={14} />{data.public
						? 'Public'
						: 'Private'}</span
				>
				<span class="fact"
					>{question_count} {question_count === 1 ? 'question' : 'questions'}</span
				>
				{#if data.questions.length > 0}
					<span class="fact"><EdIcon name="clock" size={14} />{minutes} min</span>
				{/if}
			</div>

			{#if settings_issue}
				<button type="button" class="banner" onclick={onsettings}>
					<EdIcon name="warn" size={18} />
					<span class="flex-1 text-left">{settings_issue}</span>
					<EdIcon name="right" size={20} />
				</button>
			{/if}
			{#if broken > 0}
				<button type="button" class="banner" onclick={onproblems}>
					<EdIcon name="warn" size={18} />
					<span class="flex-1 text-left"
						>{broken}
						{broken === 1 ? 'question needs' : 'questions need'} a fix</span
					>
					<EdIcon name="right" size={20} />
				</button>
			{/if}

			<div class="list-head">
				<span class="lbl">Questions</span>
				{#if data.questions.length > 1}
					<button
						type="button"
						class="link"
						aria-pressed={reorder}
						onclick={() => (reorder = !reorder)}>{reorder ? 'Done' : 'Reorder'}</button
					>
				{/if}
			</div>

			{#if data.questions.length === 0}
				<div class="empty">
					<span class="block text-lg font-black uppercase">No questions yet</span>
					<span class="mt-1 block text-[15px] text-ink-muted">
						Tap Question below, pick a type, then write it. About a minute each.
					</span>
				</div>
			{/if}

			<div class="flex flex-col gap-2">
				{#each data.questions as q, i (keyOf(q))}
					{@const slide = q.type === QuizQuestionType.SLIDE}
					{@const pts = pointsOf(q)}
					<div class="qrow" animate:flip={{ duration: 180 }}>
						<button
							type="button"
							class="qrow-main"
							disabled={reorder}
							aria-label="Edit question {i + 1}"
							onclick={() => onopen(i)}
						>
							<span class="badge" data-world={questionWorld(i)}>{i + 1}</span>
							<span class="min-w-0 flex-1">
								<span class="meta">
									<span class="truncate">{slide ? 'Slide' : questionTypeName(q)}</span>
									{#if !slide}<span class="tabular-nums">{q.time}s</span>{/if}
									{#if !slide && pts === 'double'}<span class="mini">2x</span>{/if}
									{#if issues[i]}
										<span class="text-accent-orchid"><EdIcon name="warn" size={14} /></span>
									{/if}
								</span>
								<span class="qtitle" class:italic={!slide && !plainText(q.question)}>
									{slide ? 'Content slide' : plainText(q.question) || 'No question yet'}
								</span>
							</span>
							{#if !reorder}<EdIcon name="right" size={20} />{/if}
						</button>
						{#if reorder}
							<button
								type="button"
								class="ib ib-plain"
								aria-label="Move question {i + 1} up"
								disabled={i === 0}
								onclick={() => onmove(i, i - 1)}><EdIcon name="up" size={20} /></button
							>
							<button
								type="button"
								class="ib ib-plain"
								aria-label="Move question {i + 1} down"
								disabled={i === data.questions.length - 1}
								onclick={() => onmove(i, i + 1)}><EdIcon name="down" size={20} /></button
							>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	</div>

	<footer class="bar">
		<div class="min-w-0 flex-1">
			<SaveState tone={save_tone} label={save_label} />
			<span class="block truncate text-[12px] text-ink-muted">{save_hint}</span>
		</div>
		<button type="button" class="bt-btn-primary bar-btn" onclick={onadd}>
			<EdIcon name="plus" size={20} stroke={3} /> Question
		</button>
	</footer>
</div>

<style>
	.ov {
		display: flex;
		flex-direction: column;
		height: 100dvh;
	}
	.top {
		display: flex;
		align-items: center;
		gap: 8px;
		min-height: 60px;
		padding: max(8px, env(safe-area-inset-top)) 16px 0;
	}
	.lbl {
		font-size: 12px;
		letter-spacing: 3px;
		text-transform: uppercase;
		color: var(--ink-muted);
	}
	.lbl-sm {
		font-size: 11px;
	}
	.ib {
		display: inline-grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
	}
	.ib-plain {
		background: transparent;
	}
	.ib:disabled {
		opacity: 0.3;
	}
	.ib:focus-visible,
	.link:focus-visible,
	.banner:focus-visible,
	.qrow-main:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.save-btn {
		min-height: 44px;
		padding: 0 16px;
		font-size: 14px;
		letter-spacing: 2px;
	}
	.scroll {
		min-height: 0;
		flex: 1;
		overflow-y: auto;
		overscroll-behavior: contain;
	}
	.wrap {
		padding: 12px 16px 24px;
	}
	.title-card {
		display: flex;
		align-items: flex-start;
		gap: 6px;
		padding: 12px 4px 10px 16px;
		border-radius: 20px;
		background: var(--fill-glass);
	}
	.q-title {
		margin-top: 2px;
	}
	.q-title > :global(div) {
		width: 100%;
		border: 0;
	}
	.q-title :global(.ck.ck-editor__editable_inline),
	.q-title :global([contenteditable]) {
		width: 100%;
		min-height: 36px;
		padding: 2px 0;
		border: 0 !important;
		border-radius: 8px;
		background: transparent !important;
		color: var(--ink) !important;
		font-family: var(--bt-font);
		font-size: 24px;
		font-weight: 900;
		line-height: 1.12;
		text-align: left;
		text-transform: uppercase;
		box-shadow: none !important;
	}
	.q-title :global(.ck.ck-editor__editable_inline.ck-focused),
	.q-title :global([contenteditable]:focus) {
		box-shadow: 0 2px 0 0 var(--accent-sky) !important;
		outline: none;
	}
	.q-title :global(.ck.ck-editor__editable_inline > p) {
		margin: 0;
	}
	.q-placeholder {
		position: absolute;
		left: 0;
		top: 4px;
		font-size: 24px;
		font-weight: 900;
		text-transform: uppercase;
		opacity: 0.5;
		pointer-events: none;
	}
	.facts {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 12px;
	}
	.fact {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 30px;
		padding: 0 12px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		font-size: 13px;
		font-weight: 700;
		white-space: nowrap;
	}
	.banner {
		display: flex;
		align-items: center;
		gap: 10px;
		width: 100%;
		min-height: 48px;
		margin-top: 12px;
		padding: 0 10px 0 16px;
		border-radius: 999px;
		background: rgba(215, 131, 255, 0.2);
		color: var(--accent-orchid-tint);
		font-size: 15px;
		font-weight: 700;
	}
	.list-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 44px;
		margin: 14px 0 6px;
	}
	.link {
		min-height: 44px;
		padding: 0 4px;
		font-size: 14px;
		font-weight: 700;
		color: var(--accent-sky-tint);
	}
	.empty {
		padding: 22px 18px;
		border-radius: 20px;
		background: var(--fill-glass);
	}
	.qrow {
		display: flex;
		align-items: center;
		gap: 2px;
		min-height: 72px;
		padding-right: 4px;
		border-radius: 20px;
		background: var(--fill-glass);
	}
	.qrow-main {
		display: flex;
		align-items: center;
		gap: 12px;
		flex: 1;
		min-width: 0;
		min-height: 72px;
		padding: 0 8px 0 12px;
		border-radius: 20px;
		text-align: left;
	}
	.qrow-main:disabled {
		cursor: default;
	}
	.badge {
		display: grid;
		place-items: center;
		flex: none;
		width: 40px;
		height: 40px;
		border-radius: 12px;
		background: linear-gradient(135deg, var(--ground-glow), var(--ground-mid) 70%);
		color: #fff;
		font-size: 17px;
		font-weight: 900;
	}
	.meta {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 11px;
		letter-spacing: 2.5px;
		text-transform: uppercase;
		color: var(--ink-muted);
	}
	.mini {
		padding: 1px 7px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
		font-weight: 700;
		letter-spacing: 1px;
	}
	.qtitle {
		display: block;
		margin-top: 4px;
		overflow: hidden;
		font-size: 16px;
		font-weight: 700;
		white-space: nowrap;
		text-overflow: ellipsis;
	}
	.bar {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 18px 16px max(14px, env(safe-area-inset-bottom));
		background: linear-gradient(
			to bottom,
			rgba(9, 9, 36, 0) 0,
			rgba(9, 9, 36, 0.86) 30%,
			rgba(9, 9, 36, 0.96)
		);
	}
	.bar-btn {
		min-height: 56px;
		padding: 0 24px;
		font-size: 16px;
	}
</style>
