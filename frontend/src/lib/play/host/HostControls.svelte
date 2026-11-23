<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Host control bar, outside the scaled stage so it keeps a usable size on a
	laptop. Quiet until hovered, so it does not compete with the big screen.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import { hostSound } from './sound.svelte';

	interface Props {
		page?: string;
		primary?: { label: string; action: () => void; disabled?: boolean } | null;
		paused?: boolean;
		canPause?: boolean;
		onpause?: () => void;
		onresume?: () => void;
		canEnd?: boolean;
		onend?: () => void;
		extra?: Snippet;
	}

	let {
		page,
		primary = null,
		paused = false,
		canPause = false,
		onpause,
		onresume,
		canEnd = false,
		onend,
		extra
	}: Props = $props();

	let confirmEnd = $state(false);
</script>

<div class="hc" role="toolbar" aria-label="Host controls">
	{#if page}<span class="hc-page">{page}</span>{/if}
	<button
		class="hc-icon"
		onclick={() => hostSound.toggle()}
		aria-label={hostSound.muted ? 'Turn sound on' : 'Mute sound'}
		title={hostSound.muted ? 'Sound off' : 'Sound on'}
	>
		<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
			<path d="M3 9h4l5-4v14l-5-4H3z" />
			{#if hostSound.muted}
				<path d="M16 9l5 6M21 9l-5 6" stroke="currentColor" stroke-width="2" fill="none" />
			{:else}
				<path
					d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12"
					stroke="currentColor"
					stroke-width="2"
					fill="none"
					stroke-linecap="round"
				/>
			{/if}
		</svg>
	</button>
	{@render extra?.()}
	{#if canEnd}
		{#if confirmEnd}
			<span class="hc-confirm">
				<span>End the game now?</span>
				<button
					class="bt-btn-ghost hc-btn hc-danger"
					onclick={() => {
						confirmEnd = false;
						onend?.();
					}}>End</button
				>
				<button class="bt-btn-ghost hc-btn" onclick={() => (confirmEnd = false)}>Cancel</button>
			</span>
		{:else}
			<button class="bt-btn-ghost hc-btn" onclick={() => (confirmEnd = true)}>End now</button>
		{/if}
	{/if}
	{#if canPause}
		<button
			class="bt-btn-ghost hc-btn"
			onclick={() => (paused ? onresume?.() : onpause?.())}
			title="Keyboard: P"
		>
			{paused ? 'Resume' : 'Pause'}
		</button>
	{/if}
	{#if primary}
		<button
			class="bt-btn-primary hc-btn hc-primary"
			onclick={primary.action}
			disabled={primary.disabled}
			title="Keyboard: Space or Enter">{primary.label}</button
		>
	{/if}
</div>

<style>
	.hc {
		position: fixed;
		z-index: 40;
		right: 16px;
		bottom: 16px;
		display: flex;
		align-items: center;
		gap: 8px;
		max-width: calc(100vw - 32px);
		flex-wrap: wrap;
		justify-content: flex-end;
		padding: 8px;
		border-radius: 9999px;
		background: rgba(10, 5, 31, 0.55);
		-webkit-backdrop-filter: blur(12px);
		backdrop-filter: blur(12px);
		opacity: 0.55;
		transition: opacity 200ms ease;
		font-size: 14px;
		color: var(--ink);
	}
	.hc:hover,
	.hc:focus-within {
		opacity: 1;
	}
	.hc-page {
		padding: 0 10px;
		font-variant-numeric: tabular-nums;
		color: var(--ink-muted);
	}
	.hc-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border-radius: 9999px;
		background: var(--fill-glass-mid);
		color: var(--ink);
		border: 0;
		cursor: pointer;
	}
	.hc-icon:hover {
		background: var(--fill-glass-strong);
	}
	.hc-btn {
		min-height: 40px;
		padding: 0 18px;
		font-size: 13px;
		letter-spacing: 2px;
	}
	.hc-primary {
		min-height: 44px;
		padding: 0 24px;
		font-size: 14px;
	}
	.hc-confirm {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding-left: 10px;
	}
	.hc-danger {
		background: #b4235a;
	}
	.hc-danger:hover {
		background: #cf2c69;
	}
</style>
