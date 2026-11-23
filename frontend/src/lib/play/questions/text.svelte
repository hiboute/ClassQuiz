<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Free text answer: TEXT questions, and WORD_CLOUD (1 to 30 characters,
	shown live on the big screen).
-->
<script lang="ts">
	interface Props {
		mode: 'text' | 'word_cloud';
		disabled?: boolean;
		error?: string;
		/** text to start from (kept after a refused word) */
		initial?: string;
		onsubmit: (answer: string) => void;
	}

	let { mode, disabled = false, error = '', initial = '', onsubmit }: Props = $props();

	const MAX = $derived(mode === 'word_cloud' ? 30 : 120);
	// svelte-ignore state_referenced_locally
	let value = $state(initial);
	let input: HTMLInputElement | undefined = $state();
	const clean = $derived(value.trim().replace(/\s+/g, ' '));
	const ok = $derived(clean.length >= 1 && clean.length <= MAX);

	const submit = (e?: Event) => {
		e?.preventDefault();
		if (disabled || !ok) return;
		input?.blur();
		onsubmit(clean);
	};
</script>

<form class="pt-wrap" onsubmit={submit}>
	<label class="pt-field">
		<span class="bt-eyebrow">{mode === 'word_cloud' ? 'Your word' : 'Your answer'}</span>
		<input
			bind:this={input}
			bind:value
			class="pt-input"
			data-testid="text-answer"
			maxlength={MAX}
			autocomplete="off"
			autocapitalize="off"
			spellcheck="false"
			enterkeyhint="send"
			placeholder={mode === 'word_cloud' ? 'One word or a few' : 'Type here'}
			{disabled}
		/>
		<span class="pt-hint" class:pt-error={error}>
			{#if error}
				<span role="alert">{error}</span>
			{:else if mode === 'word_cloud'}
				{clean.length} of {MAX} characters. It shows on the big screen.
			{:else}
				Spelling counts.
			{/if}
		</span>
	</label>
	<button
		type="submit"
		class="bt-btn-primary bt-btn-lg bt-btn-block"
		data-testid="answer-submit"
		disabled={disabled || !ok}
	>
		Send
	</button>
</form>

<style>
	.pt-wrap {
		margin-top: auto;
		display: flex;
		flex-direction: column;
		gap: 14px;
		padding-top: 20px;
	}
	.pt-field {
		display: block;
		border-radius: var(--radius-bt-xl);
		background: var(--fill-glass-mid);
		padding: 16px 20px;
	}
	.pt-field:focus-within {
		box-shadow: 0 0 0 3px var(--accent-sky);
	}
	.pt-input {
		display: block;
		width: 100%;
		margin-top: 8px;
		padding: 0;
		border: 0;
		outline: none;
		background: transparent;
		color: var(--ink);
		font-family: inherit;
		font-size: 28px;
		font-weight: 700;
		height: 38px;
		caret-color: var(--accent-sky);
	}
	.pt-input::placeholder {
		color: var(--ink-muted);
		opacity: 0.45;
	}
	.pt-hint.pt-error {
		color: var(--accent-orchid-tint);
	}
	.pt-hint {
		display: block;
		margin-top: 6px;
		font-size: 14px;
		color: var(--ink-muted);
	}
</style>
