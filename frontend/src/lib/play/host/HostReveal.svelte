<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Answer reveal on the big screen: correct tiles bright, others dimmed, one
	bar per answer, % correct and the fastest right answer. Also the results of
	polls, free text, range, order and word cloud questions.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { QuizQuestionType, type Question, type RangeQuizAnswer } from '$lib/quiz_types';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import AnswerTile from './AnswerTile.svelte';
	import WordCloud from './WordCloud.svelte';
	import { fitText } from './fit';
	import { countWords, isWordCloud, plain, type ResultEntry, type WordCount } from './worlds';

	interface Props {
		question: Question;
		index: number;
		total: number;
		quizTitle?: string;
		results: ResultEntry[] | null | undefined;
		words?: WordCount[];
	}

	let { question, index, total, quizTitle = '', results, words = [] }: Props = $props();

	// bars grow after the screen appears
	let grown = $state(false);
	onMount(() => {
		const id = setTimeout(() => (grown = true), 120);
		return () => clearTimeout(id);
	});

	const list = $derived(results ?? []);
	const type = $derived(question.type ?? QuizQuestionType.ABCD);
	const text = $derived(plain(question.question));
	const isPoll = $derived(type === QuizQuestionType.VOTING);
	const isTiles = $derived(
		type === QuizQuestionType.ABCD || type === QuizQuestionType.VOTING || type === QuizQuestionType.CHECK
	);
	const cloud = $derived(isWordCloud(question));

	const answers = $derived(
		Array.isArray(question.answers) ? (question.answers as { answer: string; right?: boolean }[]) : []
	);
	const counts = $derived(
		answers.map((a, i) =>
			type === QuizQuestionType.CHECK
				? list.filter((r) => String(r.answer ?? '').includes(String(i))).length
				: list.filter((r) => r.answer === a.answer).length
		)
	);
	const maxCount = $derived(Math.max(1, ...counts));
	const answered = $derived(list.length);
	const rightCount = $derived(list.filter((r) => r.right).length);
	const pct = $derived(answered ? Math.round((rightCount / answered) * 100) : 0);
	const fastest = $derived.by(() => {
		const right = list.filter((r) => r.right && Number.isFinite(Number(r.time_taken)));
		if (!right.length) return null;
		return right.reduce((a, b) => (Number(b.time_taken) < Number(a.time_taken) ? b : a));
	});
	const secs = (ms: number) => `${(Math.max(0, ms) / 1000).toFixed(1)} s`;

	const rows = $derived(Math.max(1, Math.ceil(answers.length / 2)));
	const tileH = $derived(rows === 1 ? 140 : Math.floor((308 - (rows - 1) * 20) / rows));

	// free text: grouped answers, accepted ones first
	const textGroups = $derived.by(() => {
		if (type !== QuizQuestionType.TEXT) return [];
		const map = new Map<string, { text: string; count: number; right: boolean }>();
		for (const r of list) {
			const t = String(r.answer ?? '').trim();
			if (!t) continue;
			const k = t.toLocaleLowerCase();
			const cur = map.get(k);
			if (cur) {
				cur.count += 1;
				cur.right ||= r.right;
			} else map.set(k, { text: t, count: 1, right: !!r.right });
		}
		return [...map.values()].sort((a, b) => b.count - a.count).slice(0, 6);
	});
	const textMax = $derived(Math.max(1, ...textGroups.map((g) => g.count)));

	// range: histogram of the numbers given
	const range = $derived(type === QuizQuestionType.RANGE ? (question.answers as RangeQuizAnswer) : null);
	const BINS = 24;
	const bins = $derived.by(() => {
		if (!range) return [];
		const span = Math.max(1, range.max - range.min);
		const out = Array(BINS).fill(0);
		for (const r of list) {
			const v = Number(r.answer);
			if (!Number.isFinite(v)) continue;
			const b = Math.min(BINS - 1, Math.max(0, Math.floor(((v - range.min) / span) * BINS)));
			out[b] += 1;
		}
		return out;
	});
	const binMax = $derived(Math.max(1, ...bins));
	const pos = (v: number) => (range ? ((v - range.min) / Math.max(1, range.max - range.min)) * 100 : 0);

	const cloudWords = $derived(words.length ? words : countWords(list));
</script>

<h1 class="h-title" style="width: {cloud ? 1750 : 1420}px">
	<span class="h-kicker">
		{quizTitle ? `${quizTitle}, ` : ''}question {index + 1} of {total}{cloud
			? `, ${answered} answers`
			: isPoll
				? ', votes'
				: ', results'}
	</span>
	<span class="h-headline" style="font-size: 56px" use:fitText={{ max: 56, min: 34, lines: 2, key: text }}
		>{text}</span
	>
</h1>

{#if !cloud}
	<div class="rv-stat">
		{#if isPoll}
			<div class="rv-stat__num h-num bt-text-aurora">{answered}</div>
			<div class="h-label rv-stat__label">{answered === 1 ? 'Vote' : 'Votes'}</div>
		{:else}
			<div class="rv-stat__num h-num bt-text-aurora">{pct}<small>%</small></div>
			<div class="h-label rv-stat__label">Correct</div>
		{/if}
	</div>
	<div class="rv-fast">
		{#if !isPoll && fastest}
			<span class="h-label rv-fast__label">Fastest</span>
			<span class="rv-fast__name">{fastest.username}</span>
			<span class="rv-fast__time h-num">{secs(Number(fastest.time_taken))}</span>
		{:else if !isPoll}
			<span class="h-label rv-fast__label">{answered ? 'Nobody got it' : 'No answers'}</span>
		{/if}
		{#if !isPoll && answered}
			<span class="rv-fast__of">{rightCount} of {answered} right</span>
		{/if}
	</div>
{/if}

{#if isTiles}
	<div class="rv-chart" style="--cols: {answers.length}">
		{#each answers as answer, i}
			{@const ok = isPoll || !!answer.right}
			<div class="rv-col" class:rv-col--dim={!ok}>
				<span class="rv-col__count h-num">{counts[i]}</span>
				<span
					class="rv-col__bar"
					style="height: {grown ? Math.max(8, (counts[i] / maxCount) * 210) : 8}px; background: {answerStyle(i)
						.gradient}"
				></span>
				<span class="rv-col__mark" style="background: {answerStyle(i).gradient}">
					<ShapeMark index={i} size={30} color={answerStyle(i).text} />
				</span>
			</div>
		{/each}
	</div>
	<div class="rv-tiles">
		{#each answers as answer, i}
			<AnswerTile
				index={i}
				text={answer.answer}
				height={tileH}
				fontMax={40}
				dim={!isPoll && !answer.right}
				correct={!isPoll && !!answer.right}
			/>
		{/each}
	</div>
{:else if cloud}
	<div class="rv-cloud">
		{#if cloudWords.length}
			<WordCloud words={cloudWords} width={1780} height={640} />
		{:else}
			<p class="rv-empty">No answers this time.</p>
		{/if}
	</div>
{:else if type === QuizQuestionType.TEXT}
	<div class="rv-body">
		<div class="rv-accepted">
			<span class="h-label">Accepted</span>
			<div class="rv-accepted__list">
				{#each answers as a}
					<span class="rv-accepted__item">{a.answer}</span>
				{/each}
			</div>
		</div>
		<div class="rv-bars">
			<span class="h-label">Top answers</span>
			{#each textGroups as g}
				<div class="rv-bar" class:rv-bar--dim={!g.right}>
					<span class="rv-bar__text">{g.text}</span>
					<span class="rv-bar__track"
						><span
							class:rv-bar__fill--ok={g.right}
							style="width: {grown ? (g.count / textMax) * 100 : 0}%"
						></span></span
					>
					<span class="rv-bar__n h-num">{g.count}</span>
				</div>
			{:else}
				<p class="rv-empty">No answers this time.</p>
			{/each}
		</div>
	</div>
{:else if range}
	<div class="rv-body">
		<div class="rv-range">
			<span class="h-label">Correct range</span>
			<div class="rv-range__answer h-num">
				{range.min_correct === range.max_correct
					? range.min_correct
					: `${range.min_correct} to ${range.max_correct}`}
			</div>
			<div class="rv-hist">
				<span
					class="rv-hist__band"
					style="left: {pos(range.min_correct)}%; width: {Math.max(
						0.8,
						pos(range.max_correct) - pos(range.min_correct)
					)}%"
				></span>
				{#each bins as n, b}
					<span
						class="rv-hist__bin"
						style="left: {(b / BINS) * 100}%; width: {100 / BINS}%; height: {grown ? (n / binMax) * 100 : 0}%"
					></span>
				{/each}
			</div>
			<div class="rv-hist__axis"><span>{range.min}</span><span>{range.max}</span></div>
		</div>
	</div>
{:else if type === QuizQuestionType.ORDER}
	<div class="rv-body">
		<span class="h-label">Right order</span>
		<ol class="rv-order">
			{#each answers as a, i}
				<li class="rv-order__item">
					<span class="rv-order__n h-num">{i + 1}</span>
					<span class="rv-order__text">{a.answer}</span>
				</li>
			{/each}
		</ol>
	</div>
{/if}

<style>
	.rv-stat {
		position: absolute;
		z-index: 3;
		left: 1540px;
		top: 64px;
		width: 316px;
		height: 316px;
		border-radius: 50%;
		background: var(--fill-deep);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 18px;
	}
	.rv-stat__num {
		font-size: 136px;
		line-height: 1;
	}
	.rv-stat__num small {
		font-size: 64px;
	}
	.rv-stat__label {
		font-size: 20px;
	}
	.rv-fast {
		position: absolute;
		z-index: 3;
		left: 1520px;
		top: 404px;
		width: 356px;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}
	.rv-fast__label {
		font-size: 18px;
		color: var(--ink-muted);
	}
	.rv-fast__name {
		font-size: 34px;
		font-weight: 900;
		max-width: 356px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.rv-fast__time {
		font-size: 48px;
	}
	.rv-fast__of {
		margin-top: 6px;
		font-size: 22px;
		color: var(--ink-muted);
	}
	.rv-chart {
		position: absolute;
		z-index: 3;
		left: 84px;
		width: 1400px;
		top: 290px;
		height: 320px;
		display: grid;
		grid-template-columns: repeat(var(--cols), minmax(0, 200px));
		justify-content: center;
		gap: 48px;
		align-items: end;
	}
	.rv-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		transition: opacity 500ms ease;
	}
	.rv-col--dim {
		opacity: 0.35;
	}
	.rv-col__count {
		font-size: 56px;
		line-height: 1;
	}
	.rv-col__bar {
		display: block;
		width: 100%;
		border-radius: 12px 12px 0 0;
		transition: height 900ms cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.rv-col__mark {
		width: 100%;
		height: 52px;
		margin-top: -12px;
		border-radius: 0 0 12px 12px;
		display: grid;
		place-items: center;
	}
	.rv-tiles {
		position: absolute;
		z-index: 3;
		left: 70px;
		right: 70px;
		top: 640px;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 20px 28px;
	}
	.rv-cloud {
		position: absolute;
		z-index: 3;
		left: 70px;
		right: 70px;
		top: 290px;
		height: 640px;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	.rv-empty {
		font-size: 32px;
		color: var(--ink-muted);
	}
	.rv-body {
		position: absolute;
		z-index: 3;
		left: 84px;
		width: 1400px;
		top: 290px;
		bottom: 130px;
		display: flex;
		flex-direction: column;
		gap: 30px;
	}
	.rv-accepted__list {
		margin-top: 14px;
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
	}
	.rv-accepted__item {
		height: 64px;
		display: inline-flex;
		align-items: center;
		padding: 0 28px;
		border-radius: 9999px;
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		color: var(--ink-dark);
		font-size: 30px;
		font-weight: 900;
		text-transform: uppercase;
	}
	.rv-bars {
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.rv-bar {
		display: grid;
		grid-template-columns: 460px 1fr 110px;
		align-items: center;
		gap: 28px;
		height: 64px;
		padding: 0 28px;
		border-radius: 18px;
		background: var(--fill-deep);
	}
	.rv-bar--dim {
		opacity: 0.6;
	}
	.rv-bar__text {
		font-size: 30px;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.rv-bar__track {
		height: 16px;
		background: var(--fill-glass);
	}
	.rv-bar__track span {
		display: block;
		height: 100%;
		background: var(--fill-glass-strong);
		transition: width 900ms cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.rv-bar__track span.rv-bar__fill--ok {
		background: linear-gradient(90deg, var(--accent-blue), var(--accent-sky) 55%, var(--accent-green));
	}
	.rv-bar__n {
		font-size: 44px;
		text-align: right;
	}
	.rv-range {
		padding: 44px 56px;
		border-radius: 25px;
		background: var(--fill-deep);
	}
	.rv-range__answer {
		margin-top: 18px;
		font-size: 120px;
		line-height: 1;
	}
	.rv-hist {
		position: relative;
		margin-top: 40px;
		height: 200px;
		border-bottom: 0;
		background: linear-gradient(var(--fill-glass-mid), var(--fill-glass-mid)) bottom / 100% 4px no-repeat;
	}
	.rv-hist__band {
		position: absolute;
		top: 0;
		bottom: 0;
		border-radius: 12px;
		background: linear-gradient(180deg, rgba(39, 190, 130, 0.12), rgba(39, 190, 130, 0.38));
	}
	.rv-hist__bin {
		position: absolute;
		bottom: 0;
		box-sizing: border-box;
		border-left: 3px solid transparent;
		border-right: 3px solid transparent;
		background-clip: padding-box;
		background-color: var(--accent-sky);
		transition: height 900ms cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.rv-hist__axis {
		display: flex;
		justify-content: space-between;
		margin-top: 12px;
		font-size: 28px;
		font-weight: 700;
	}
	.rv-order {
		margin: 0;
		padding: 0;
		list-style: none;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 18px 28px;
	}
	.rv-order__item {
		display: flex;
		align-items: center;
		gap: 28px;
		height: 110px;
		padding: 0 34px;
		border-radius: 25px;
		background: var(--fill-deep);
	}
	.rv-order__n {
		font-size: 72px;
		width: 70px;
		text-align: center;
	}
	.rv-order__text {
		font-size: 40px;
		font-weight: 900;
		text-transform: uppercase;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
