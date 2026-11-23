<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	ORDER: tap the items in the right order (1, 2, 3...). Tap a numbered item
	again to take it back. Once every item has a place, lock the order in.
-->
<script lang="ts">
	interface Props {
		answers: Array<{ answer: string }>;
		disabled?: boolean;
		onsubmit: (ordered: Array<{ answer: string }>, label: string) => void;
	}

	let { answers, disabled = false, onsubmit }: Props = $props();

	// picked[k] = index in `answers` of the item placed at position k
	let picked: number[] = $state([]);
	const done = $derived(picked.length === answers.length && answers.length > 0);

	const tap = (i: number) => {
		if (disabled) return;
		const at = picked.indexOf(i);
		if (at === -1) {
			picked = [...picked, i];
		} else {
			// take this one and everything placed after it back
			picked = picked.slice(0, at);
		}
	};

	const submit = () => {
		if (disabled || !done) return;
		const ordered = picked.map((i) => ({ answer: answers[i].answer }));
		onsubmit(ordered, ordered.map((o) => o.answer).join(', '));
	};
</script>

<div class="po-wrap">
	<p class="po-help">
		{done ? 'All placed. Tap one to change it.' : `Tap item ${picked.length + 1} of ${answers.length}`}
	</p>
	<ol class="po-list" data-testid="answer-list">
		{#each answers as answer, i (i)}
			{@const place = picked.indexOf(i)}
			<li>
				<button
					type="button"
					class="po-item"
					class:po-placed={place !== -1}
					data-testid="answer-tile"
					data-answer-index={i}
					aria-pressed={place !== -1}
					{disabled}
					onclick={() => tap(i)}
				>
					<span class="po-rank bt-num" aria-hidden={place === -1}>
						{place === -1 ? '' : place + 1}
					</span>
					<span class="po-label">{answer.answer}</span>
				</button>
			</li>
		{/each}
	</ol>
	<div class="po-actions">
		<button
			type="button"
			class="bt-btn-ghost po-reset"
			disabled={disabled || picked.length === 0}
			onclick={() => (picked = [])}>Reset</button
		>
		<button
			type="button"
			class="bt-btn-primary bt-btn-lg po-submit"
			data-testid="answer-submit"
			disabled={disabled || !done}
			onclick={submit}>Lock in</button
		>
	</div>
</div>

<style>
	.po-wrap {
		margin-top: auto;
		display: flex;
		flex-direction: column;
		gap: 12px;
		padding-top: 16px;
	}
	.po-help {
		margin: 0;
		font-size: 15px;
		color: var(--ink-muted);
	}
	.po-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.po-item {
		width: 100%;
		min-height: 72px;
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 10px 16px 10px 12px;
		border: 0;
		border-radius: var(--radius-bt-xl);
		background: var(--fill-glass-mid);
		color: var(--ink);
		font: 700 20px/1.15 var(--bt-font);
		text-align: left;
		cursor: pointer;
		user-select: none;
		-webkit-user-select: none;
		transition:
			background-color 120ms ease,
			transform 120ms ease;
	}
	.po-item:active:not(:disabled) {
		transform: scale(0.98);
	}
	.po-placed {
		background: var(--fill-deep);
	}
	.po-rank {
		flex: none;
		width: 52px;
		height: 52px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-bt-md);
		box-shadow: inset 0 0 0 2px rgba(254, 255, 255, 0.35);
		font-size: 28px;
		line-height: 1;
	}
	.po-placed .po-rank {
		box-shadow: none;
		background: linear-gradient(120deg, var(--accent-sky), var(--accent-green));
		color: var(--ink-dark);
	}
	.po-label {
		flex: 1 1 auto;
		min-width: 0;
		overflow-wrap: anywhere;
	}
	.po-actions {
		display: flex;
		gap: 10px;
		margin-top: 4px;
	}
	.po-reset {
		min-height: 64px;
		padding: 0 22px;
	}
	.po-submit {
		flex: 1 1 auto;
	}
</style>
