<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { dataSchema } from '$lib/yupSchemas';
	import type { EditorData } from './quiz_types';
	import Sidebar from '$lib/editor/sidebar.svelte';
	import SettingsCard from '$lib/editor/settings-card.svelte';
	import QuizCard from '$lib/editor/card.svelte';
	import Loading from '$lib/editor/Loading.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import World from '$lib/brand/World.svelte';
	import { plainText, questionIssue } from '$lib/editor/editor_meta';
	import { getLocalization } from '$lib/i18n';
	import { MediaQuery } from 'svelte/reactivity';
	import MobileEditor from '$lib/editor/mobile/MobileEditor.svelte';

	const { t } = getLocalization();

	let schemaInvalid = $state(false);
	let yupErrorMessage = $state('');
	let errorCount = $state(0);
	let saving = $state(false);

	interface Props {
		data: EditorData;
		quiz_id: string | null;
	}

	let { data = $bindable(), quiz_id = $bindable() }: Props = $props();
	// below the md breakpoint the phone layout takes over (same data and save)
	const phone = new MediaQuery('max-width: 767.98px', false);
	let selected_question = $state(-1);

	const validateInput = async (snapshot: EditorData) => {
		try {
			await dataSchema.validate(snapshot, { abortEarly: false });
			schemaInvalid = false;
			yupErrorMessage = '';
			errorCount = 0;
		} catch (err) {
			schemaInvalid = true;
			yupErrorMessage = err?.errors ? err.errors[0] : 'Something in the quiz is not valid';
			errorCount = err?.errors?.length ?? 1;
		}
	};
	$effect(() => {
		// snapshot reads the whole quiz, so any edit re-validates
		validateInput($state.snapshot(data) as EditorData);
	});
	let edit_id: string = $state();
	let confirm_to_leave = true;

	const getEditID = async () => {
		let res: Response;
		if (quiz_id === null) {
			res = await fetch(`/api/v1/editor/start?edit=false`, {
				method: 'POST'
			});
		} else {
			res = await fetch(`/api/v1/editor/start?edit=true&quiz_id=${quiz_id}`, {
				method: 'POST'
			});
		}
		if (res.status === 200) {
			const json = await res.json();
			edit_id = json.token;
		} else {
			alert('Could not open the editor. Please reload the page.');
		}
	};

	const confirmUnload = (event: BeforeUnloadEvent) => {
		if (!confirm_to_leave) {
			return;
		}
		event.preventDefault();
		event.returnValue = 'Are you sure you want to leave?';
		localStorage.setItem('edit_game', JSON.stringify(data));
		return 'unload';
	};
	const saveQuiz = async (e?: Event) => {
		e?.preventDefault();
		if (schemaInvalid || saving) {
			return;
		}
		saving = true;
		const res = await fetch(`/api/v1/editor/finish?edit_id=${edit_id}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(data)
		});
		if (res.ok) {
			confirm_to_leave = false;
			window.location.href = '/dashboard';
		} else {
			saving = false;
			alert('The quiz could not be saved. Check the highlighted fields and try again.');
		}
	};

	const title_text = $derived(plainText(data.title));
	// where the first problem is, so the status can jump to it
	const first_issue = $derived.by(() => {
		for (let i = 0; i < data.questions.length; i++) {
			const issue = questionIssue(data.questions[i]);
			if (issue) return { index: i, issue };
		}
		return null;
	});
	const go_to_issue = () => {
		if (!schemaInvalid) return;
		selected_question = first_issue && !yupErrorMessage.match(/title|description/i)
			? first_issue.index
			: -1;
	};
	const question_count = $derived(data.questions.filter((q) => q.type !== 'SLIDE').length);
</script>

<svelte:window onbeforeunload={confirmUnload} />
<World world="midnight" fullscreen={false} class="h-dvh">
	{#await getEditID()}
		<div class="grid h-full place-items-center">
			<Loading label="Opening the editor" />
		</div>
	{:then _}
		{#if phone.current}
			<MobileEditor
				bind:data
				bind:edit_id
				schema_invalid={schemaInvalid}
				{saving}
				onsave={() => saveQuiz()}
			/>
		{:else}
			<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
			<form
				onsubmit={saveQuiz}
				onkeydown={(e) => {
					// Enter in a text field must not save and leave the editor
					if (e.key === 'Enter' && (e.target as HTMLElement)?.tagName === 'INPUT') {
						e.preventDefault();
					}
				}}
				class="grid h-full grid-rows-[minmax(0,38vh)_minmax(0,1fr)] md:grid-rows-1 md:grid-cols-[264px_minmax(0,1fr)] xl:grid-cols-[312px_minmax(0,1fr)]"
			>
				<aside class="min-h-0">
					<Sidebar bind:data bind:selected_question />
				</aside>
				<main class="flex min-h-0 min-w-0 flex-col">
					<header class="flex flex-wrap items-center gap-x-5 gap-y-2 px-5 pt-5 pb-3 lg:px-8">
						<div class="min-w-[180px] flex-1">
							<span class="bt-eyebrow text-[11px] text-ink-muted">
								Quiz editor{#if quiz_id === null}, new quiz{/if}
							</span>
							<h1 class="truncate text-xl leading-tight font-black uppercase lg:text-2xl">
								{title_text || 'Untitled quiz'}
							</h1>
						</div>
						<button
							type="button"
							class="order-last flex w-full max-w-full items-center gap-2 rounded-full px-4 py-2 text-left text-sm xl:order-none xl:w-auto"
							class:status-bad={schemaInvalid}
							class:status-good={!schemaInvalid}
							aria-live="polite"
							title={schemaInvalid ? 'Show me' : undefined}
							onclick={go_to_issue}
						>
							<EdIcon name={schemaInvalid ? 'warn' : 'check'} size={16} />
							<span class="truncate">
								{#if schemaInvalid}
									{#if first_issue && !yupErrorMessage.match(/title|description/i)}Question {first_issue.index +
											1}: {first_issue.issue}{:else}{yupErrorMessage}{/if}{#if errorCount > 1}<span
											class="opacity-70"
										>
											(+{errorCount - 1} more)</span
										>{/if}
								{:else}
									Ready to save, {question_count}
									{question_count === 1 ? 'question' : 'questions'}
								{/if}
							</span>
						</button>
						<a href="/dashboard" class="bt-btn-ghost exit-btn">Exit</a>
						<button class="bt-btn-primary" disabled={schemaInvalid || saving} type="submit">
							<EdIcon name="save" size={18} />
							<span>{saving ? 'Saving' : $t('words.save')}</span>
						</button>
					</header>
					<div class="min-h-0 flex-1 overflow-y-auto px-5 pb-8 lg:px-8">
						{#if selected_question === -1}
							<SettingsCard bind:data bind:edit_id />
						{:else}
							<QuizCard bind:data bind:selected_question bind:edit_id />
						{/if}
					</div>
				</main>
			</form>
		{/if}
	{/await}
</World>

<style>
	.status-bad {
		background: rgba(249, 130, 250, 0.16);
		color: #ffd3fb;
	}
	.status-good {
		background: rgba(39, 190, 130, 0.16);
		color: var(--accent-green-tint);
	}
	.exit-btn {
		min-height: 44px;
		padding: 0 20px;
		font-size: 14px;
		letter-spacing: 2px;
	}
</style>
