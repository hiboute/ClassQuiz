<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	The quiz editor below the phone breakpoint: an overview screen, a full
	screen editor per question, and bottom sheets for the question type and the
	quiz settings. Same data, validation and save as the desktop editor; only
	the layout differs. The open question is kept in the history state, so the
	phone's back gesture returns to the overview.
-->
<script lang="ts">
	import type { EditorData } from '$lib/quiz_types';
	import { QuizQuestionType } from '$lib/quiz_types';
	import { pushState, replaceState } from '$app/navigation';
	import { page } from '$app/state';
	import { reach, type Schema } from 'yup';
	import { dataSchema } from '$lib/yupSchemas';
	import SettingsCard from '$lib/editor/settings-card.svelte';
	import MobileOverview from './MobileOverview.svelte';
	import MobileQuestion from './MobileQuestion.svelte';
	import TypeSheet from './TypeSheet.svelte';
	import Sheet from './Sheet.svelte';
	import {
		choiceKeyOf,
		newQuestion,
		newSlide,
		plainText,
		questionIssue,
		type QuestionChoice
	} from '$lib/editor/editor_meta';

	interface Props {
		data: EditorData;
		edit_id: string;
		schema_invalid: boolean;
		saving: boolean;
		onsave: () => void;
	}

	let { data = $bindable(), edit_id = $bindable(), schema_invalid, saving, onsave }: Props =
		$props();

	// ---- which screen: -1 is the overview, otherwise the open question
	let pushed = false;
	const current = $derived.by(() => {
		const i = Number((page.state as { mq?: number }).mq ?? -1);
		return Number.isInteger(i) && i >= 0 && i < data.questions.length ? i : -1;
	});
	const open_question = (i: number) => {
		if (current === -1) {
			pushState('', { mq: i });
			pushed = true;
		} else {
			replaceState('', { mq: i });
		}
	};
	const to_overview = () => {
		if (current === -1) return;
		if (pushed) {
			pushed = false;
			history.back();
		} else {
			replaceState('', {});
		}
	};

	// ---- problems
	const issues = $derived(data.questions.map((q) => questionIssue(q)));
	const titleSchema = reach(dataSchema, 'title') as Schema;
	const descriptionSchema = reach(dataSchema, 'description') as Schema;
	const settings_issue = $derived.by(() => {
		if (!titleSchema.isValidSync(data.title)) {
			return plainText(data.title) ? 'The title needs 3 to 300 characters' : 'Give the quiz a title';
		}
		if (!descriptionSchema.isValidSync(data.description)) {
			return String(data.description ?? '').trim()
				? 'The description needs 3 to 500 characters'
				: 'Add a short description';
		}
		return null;
	});
	const problem_count = $derived(issues.filter(Boolean).length + (settings_issue ? 1 : 0));

	const save_tone = $derived<'bad' | 'ok' | 'busy'>(
		saving ? 'busy' : schema_invalid ? 'bad' : 'ok'
	);
	const save_label = $derived(saving ? 'Saving' : schema_invalid ? 'Not saved' : 'Ready to save');
	const save_hint = $derived(
		saving
			? 'Taking you to the dashboard'
			: data.questions.length === 0
				? 'Add a question to save'
				: problem_count > 0
					? `Fix ${problem_count} to save`
					: 'Tap Save at the top'
	);

	// next problem after the open question, then the quiz settings
	const show_problems = () => {
		const n = data.questions.length;
		for (let k = 1; k <= n; k++) {
			const i = (Math.max(current, -1) + k + n) % n;
			if (i !== current && issues[i]) {
				open_question(i);
				return;
			}
		}
		if (settings_issue) {
			to_overview();
			sheet = 'settings';
		}
	};

	// ---- sheets
	let sheet: null | 'add' | 'change' | 'settings' = $state(null);
	let title_rev = $state(0);
	const close_sheet = () => {
		if (sheet === 'settings') title_rev++;
		sheet = null;
	};

	const add = (q: EditorData['questions'][number]) => {
		data.questions = [...data.questions, q];
		sheet = null;
		open_question(data.questions.length - 1);
	};

	const has_answer_text = (answers: unknown) =>
		Array.isArray(answers) &&
		answers.some((a: { answer?: string }) => (a?.answer ?? '').trim() !== '');

	const change_type = (c: QuestionChoice) => {
		const i = current;
		const q = data.questions[i];
		sheet = null;
		if (!q || choiceKeyOf(q) === c.key) return;
		const quiz_kinds: string[] = [QuizQuestionType.ABCD, QuizQuestionType.CHECK];
		const keep =
			c.key !== 'truefalse' &&
			quiz_kinds.includes(String(q.type ?? QuizQuestionType.ABCD)) &&
			quiz_kinds.includes(c.type);
		if (keep) {
			// multiple choice and multiple select share their answers
			q.type = c.type;
			return;
		}
		if (has_answer_text(q.answers) && !confirm(`Change to ${c.name}? The answers will be cleared.`)) {
			return;
		}
		q.type = c.type;
		q.answers = c.answers();
		if (c.type === QuizQuestionType.WORD_CLOUD) q.points = 'none';
		else if (c.type === QuizQuestionType.VOTING) q.points = 'standard';
		if (c.time && c.key === 'truefalse') q.time = c.time;
	};

	// ---- list edits
	const move = (from: number, to: number) => {
		if (to < 0 || to >= data.questions.length) return;
		const arr = [...data.questions];
		[arr[from], arr[to]] = [arr[to], arr[from]];
		data.questions = arr;
		if (current === from) open_question(to);
	};
	const duplicate = (i: number) => {
		const copy = JSON.parse(JSON.stringify($state.snapshot(data.questions[i])));
		const arr = [...data.questions];
		arr.splice(i + 1, 0, copy);
		data.questions = arr;
		open_question(i + 1);
	};
	const remove = (i: number) => {
		const label = plainText(data.questions[i].question) || 'this question';
		if (!confirm(`Delete "${label}"?`)) return;
		const arr = [...data.questions];
		arr.splice(i, 1);
		if (arr.length === 0) {
			to_overview();
			data.questions = arr;
			return;
		}
		data.questions = arr;
		open_question(Math.min(i, arr.length - 1));
	};

	const after_label = $derived(
		data.questions.length === 0 ? 'First question' : `Add after question ${data.questions.length}`
	);
</script>

<MobileOverview
	bind:data
	{issues}
	{settings_issue}
	{problem_count}
	{save_tone}
	{save_label}
	{save_hint}
	{saving}
	{title_rev}
	can_save={!schema_invalid && !saving}
	{onsave}
	onopen={open_question}
	onadd={() => (sheet = 'add')}
	onsettings={() => (sheet = 'settings')}
	onproblems={show_problems}
	onmove={move}
/>

{#if current !== -1}
	<MobileQuestion
		bind:data
		bind:edit_id
		index={current}
		{issues}
		{problem_count}
		{save_tone}
		{save_label}
		onback={to_overview}
		ongo={open_question}
		onadd={() => (sheet = 'add')}
		onchangetype={() => (sheet = 'change')}
		onproblems={show_problems}
		onmove={move}
		onduplicate={duplicate}
		ondelete={remove}
	/>
{/if}

{#if sheet === 'add'}
	<TypeSheet
		kicker={after_label}
		onpick={(c) => add(newQuestion(c))}
		onslide={() => add(newSlide())}
		onclose={close_sheet}
	/>
{:else if sheet === 'change'}
	<TypeSheet
		kicker="Change question {current + 1}"
		current={choiceKeyOf(data.questions[current])}
		allow_slide={false}
		onpick={change_type}
		onclose={close_sheet}
	/>
{:else if sheet === 'settings'}
	<Sheet kicker="Quiz settings" title="Title and details" tall onclose={close_sheet}>
		<div class="settings">
			<SettingsCard bind:data bind:edit_id />
		</div>
	</Sheet>
{/if}

<style>
	/* the desktop settings card, flattened into the sheet */
	.settings :global(section) {
		padding: 16px;
	}
	.settings :global(textarea) {
		font-size: 16px;
	}
</style>
