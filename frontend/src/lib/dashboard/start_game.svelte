<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Start-game dialog. One game mode (live tiles: question on the big screen,
	coloured shapes on the phones). The get-ready countdown and the room lock
	are set from the host lobby, not here.
-->
<script lang="ts">
	import { captcha_enabled } from '$lib/config';
	import { onMount } from 'svelte';
	import Modal from '$lib/components/organiser/Modal.svelte';
	import Toggle from '$lib/components/organiser/Toggle.svelte';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { ANSWERS } from '$lib/brand/answers';

	interface Props {
		quiz_id: string | null;
		quiz_title?: string;
		question_count?: number;
	}

	let { quiz_id = $bindable(), quiz_title = '', question_count }: Props = $props();

	// The backend name of the live tiles mode. Never shown to people.
	const GAME_MODE = 'kahoot';

	let captcha_selected = $state(false);
	let randomized_answers = $state(false);
	let custom_field = $state('');
	let show_more = $state(false);
	let loading = $state(false);
	let error = $state('');

	onMount(() => {
		try {
			custom_field = localStorage.getItem('custom_field') ?? '';
			const saved = JSON.parse(localStorage.getItem('start_game_options') ?? '{}');
			if (typeof saved.randomized_answers === 'boolean')
				randomized_answers = saved.randomized_answers;
		} catch {
			/* storage unavailable: keep the defaults */
		}
	});

	const close = () => {
		if (!loading) quiz_id = null;
	};

	const start_game = async (id: string) => {
		loading = true;
		error = '';
		try {
			localStorage.setItem('custom_field', custom_field);
			localStorage.setItem(
				'start_game_options',
				JSON.stringify({ randomized_answers })
			);
		} catch {
			/* ignore */
		}
		const params = new URLSearchParams({
			captcha_enabled: captcha_enabled && captcha_selected ? 'True' : 'False',
			game_mode: GAME_MODE,
			custom_field,
			cqcs_enabled: 'False',
			randomize_answers: randomized_answers ? 'True' : 'False'
		});
		let res: Response;
		try {
			res = await fetch(`/api/v1/quiz/start/${id}?${params}`, { method: 'POST' });
		} catch {
			error = 'The server could not be reached. Check the connection and try again.';
			loading = false;
			return;
		}
		if (res.status === 401) {
			window.location.assign('/account/login?returnTo=/dashboard');
			return;
		}
		if (res.status !== 200) {
			error = `The game could not start (error ${res.status}). Try again in a moment.`;
			loading = false;
			return;
		}
		const data = await res.json();
		try {
			const plausible = (window as any).plausible;
			if (typeof plausible === 'function')
				plausible('Started Game', { props: { quiz_id: id, game_id: data.game_id } });
		} catch {
			/* analytics is optional */
		}
		const next = new URLSearchParams({
			token: data.game_id,
			pin: data.game_pin,
			connect: '1',
			cqc_code: String(data.cqc_code ?? '')
		});
		window.location.assign(`/admin?${next}`);
	};
</script>

<Modal label="Start a live game" world="indigo" onclose={close}>
	<div class="px-6 pt-8 pb-6 sm:px-10 sm:pt-10">
		<span class="bt-eyebrow text-ink-muted mb-3">Start a live game</span>
		{#if quiz_title}
			<span class="bt-kicker text-lg">{@html quiz_title}</span>
		{/if}
		<h2 class="bt-headline text-[30px] sm:text-[40px]">Ready to host</h2>
		{#if question_count !== undefined}
			<p class="mt-2 text-ink-muted">
				{question_count}
				{question_count === 1 ? 'question' : 'questions'}, shown on the big screen.
			</p>
		{/if}

		<!-- the one game mode -->
		<div class="bt-glass bt-glass-faint mt-6 p-5 flex items-center gap-5" aria-label="Game mode">
			<div class="grid grid-cols-2 gap-1.5 shrink-0" aria-hidden="true">
				{#each ANSWERS as a, i}
					<span class="{a.className} !rounded-[9px] h-9 w-9 justify-center">
						<ShapeMark shape={a.shape} index={i} size={16} color={a.text} />
					</span>
				{/each}
			</div>
			<div class="min-w-0">
				<span class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted">Game mode</span>
				<p class="font-black uppercase text-lg leading-tight mt-1">Live tiles</p>
				<p class="text-sm text-ink-muted mt-1">
					Questions and answers on the big screen, players tap the matching shape on their
					phone. Faster right answers score more.
				</p>
			</div>
		</div>

		<div class="mt-4 flex flex-col gap-2">
			<Toggle
				id="randomized-answers-toggle"
				bind:checked={randomized_answers}
				label="Shuffle answers"
				hint="Answer order changes from the one in the editor."
			/>
			{#if captcha_enabled}
				<Toggle
					id="captcha-toggle"
					bind:checked={captcha_selected}
					label="Captcha on join"
					hint="Players solve a captcha before they can join. Slows joining down."
				/>
			{/if}
		</div>
		<p class="mt-3 text-sm text-ink-muted">
			The get ready countdown and the room lock are in the lobby, once the game is open.
		</p>

		<button
			type="button"
			class="mt-4 text-sm text-ink-muted hover:text-ink underline underline-offset-4"
			aria-expanded={show_more}
			onclick={() => (show_more = !show_more)}
		>
			{show_more ? 'Hide extra options' : 'Extra options'}
		</button>
		{#if show_more}
			<div class="mt-3">
				<label for="custom-field" class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted mb-2"
					>Extra field asked at join</label
				>
				<input
					id="custom-field"
					bind:value={custom_field}
					class="bt-input !text-base"
					placeholder="Leave empty for none, for example Employee ID"
				/>
			</div>
		{/if}

		{#if error}
			<p class="mt-4 rounded-[18px] bg-[#ff4d6d]/20 px-4 py-3 text-sm" role="alert">{error}</p>
		{/if}
	</div>

	<div
		class="sticky bottom-0 flex flex-col-reverse sm:flex-row gap-3 px-6 pb-6 pt-4 sm:px-10 sm:pb-10 bg-gradient-to-t from-[var(--ground)] via-[var(--ground)]/90 to-transparent"
	>
		<button type="button" class="bt-btn-ghost sm:w-auto w-full" onclick={close} disabled={loading}
			>Cancel</button
		>
		<button
			type="button"
			class="bt-btn-primary bt-btn-lg flex-1"
			disabled={loading || !quiz_id}
			onclick={() => quiz_id && start_game(quiz_id)}
		>
			{#if loading}
				<svg class="h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true"
					><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-opacity=".25" stroke-width="3" /><path
						d="M21 12a9 9 0 0 0-9-9"
						stroke="currentColor"
						stroke-width="3"
						stroke-linecap="round"
					/></svg
				>
				<span class="sr-only">Starting</span>
			{:else}
				Open the lobby
			{/if}
		</button>
	</div>
</Modal>
