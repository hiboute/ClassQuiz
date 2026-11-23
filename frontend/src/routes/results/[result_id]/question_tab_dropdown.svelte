<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { QuizQuestionType } from '$lib/quiz_types';
	import { getLocalization } from '$lib/i18n';
	import type { Question } from '$lib/quiz_types';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';

	const { t } = getLocalization();

	interface Answer {
		username: string;
		answer: string;
		right: boolean;
		time_taken: number;
		score: number;
	}

	interface Props {
		question: any;
		answers: Answer[];
	}

	let { question, answers }: Props = $props();

	// Polls and word clouds have no right answer and give no points
	const no_grade = $derived(
		question.type === QuizQuestionType.VOTING || question.type === QuizQuestionType.WORD_CLOUD
	);
	const words = $derived.by(() => {
		if (question.type !== QuizQuestionType.WORD_CLOUD) return [];
		const map = new Map<string, { text: string; count: number }>();
		for (const a of answers ?? []) {
			const text = String(a.answer ?? '').trim().replace(/\s+/g, ' ');
			if (!text) continue;
			const key = text.toLocaleLowerCase();
			const cur = map.get(key);
			if (cur) cur.count += 1;
			else map.set(key, { text, count: 1 });
		}
		return [...map.values()].sort((a, b) => b.count - a.count || a.text.localeCompare(b.text));
	});

	const get_answer_count_for_answer = (answer: string): number => {
		let count = 0;
		let answer_id = 0;
		if (question.type === QuizQuestionType.CHECK) {
			for (let i = 0; i < question.answers.length; i++) {
				if (answer === question.answers[i].answer) {
					answer_id = i;
					break;
				}
			}
		}
		for (let i = 0; i < answers.length; i++) {
			const a = answers[i];
			if (question.type === QuizQuestionType.CHECK) {
				if (a.answer.includes(String(answer_id))) {
					count++;
				}
			} else if (a.answer === answer) {
				count++;
			}
		}
		return count;
	};
</script>

<div class="flex flex-col gap-6">
	{#if question.type !== QuizQuestionType.ORDER && question.type !== QuizQuestionType.RANGE && Array.isArray(question.answers)}
		<ul class="flex flex-col gap-2">
			{#each question.answers as answer, ai}
				{@const n = get_answer_count_for_answer(answer.answer)}
				{@const style = answerStyle(ai)}
				{@const show_right =
					!no_grade && question.type !== QuizQuestionType.TEXT}
				<li class="flex items-center gap-3">
					<span class="{style.className} !rounded-[9px] h-8 w-8 shrink-0 justify-center">
						<ShapeMark shape={style.shape} size={14} color={style.text} />
					</span>
					<div class="flex-1 min-w-0">
						<div class="flex justify-between gap-3 text-sm">
							<span class="truncate" class:font-bold={show_right && answer.right}>{answer.answer}</span>
							<span class="tabular-nums shrink-0">
								{n}
								{#if show_right && answer.right}
									<span class="ms-2 text-[var(--accent-green-tint)] uppercase text-[11px] tracking-[2px]"
										>Right</span
									>
								{/if}
							</span>
						</div>
						<div class="mt-1.5 h-2 rounded-full bg-white/10 overflow-hidden">
							<div
								class="h-full rounded-full"
								style="width: {answers.length ? (n / answers.length) * 100 : 0}%; background: {style.gradient}"
							></div>
						</div>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
	{#if words.length}
		<ul class="flex flex-wrap gap-2" data-testid="result-words">
			{#each words as w}
				<li class="rounded-full bg-white/10 px-4 py-2">
					<span class="font-bold">{w.text}</span>
					<span class="tabular-nums text-ink-muted ms-1">{w.count}</span>
				</li>
			{/each}
		</ul>
	{/if}
	<div class="overflow-x-auto -mx-2">
		<table class="min-w-full text-sm">
			<thead>
				<tr class="text-ink-muted">
					<th class="px-2 py-2 text-start font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
						>{$t('result_page.player_name')}</th
					>
					{#if !no_grade}
						<th class="px-2 py-2 text-end font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
							>{$t('words.score')}</th
						>
					{/if}
					<th class="px-2 py-2 text-end font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
						>{$t('result_page.time_taken')}</th
					>
					<th class="px-2 py-2 text-start font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
						>{$t('words.answer')}</th
					>
					{#if !no_grade}
						<th class="px-2 py-2 text-start font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
							>{$t('words.correct')}</th
						>
					{/if}
				</tr>
			</thead>
			<tbody>
				{#each answers as answer}
					<tr class="border-t border-white/10">
						<td class="px-2 py-2.5 font-bold whitespace-nowrap">{answer.username}</td>
						{#if !no_grade}
							<td class="px-2 py-2.5 text-end tabular-nums">{answer.score}</td>
						{/if}
						<td class="px-2 py-2.5 text-end tabular-nums whitespace-nowrap">{(answer.time_taken / 1000).toFixed(2)} s</td>
						<td class="px-2 py-2.5">{answer.answer}</td>
						{#if !no_grade}
							<td class="px-2 py-2.5">
								{#if answer.right}
									<span class="text-[var(--accent-green-tint)]">Right</span>
								{:else}
									<span class="text-ink-muted">Wrong</span>
								{/if}
							</td>
						{/if}
					</tr>
				{:else}
					<tr><td colspan="5" class="px-2 py-3 text-ink-muted">Nobody answered this question.</td></tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
