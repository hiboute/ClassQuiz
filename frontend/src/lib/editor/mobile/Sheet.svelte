<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Bottom sheet of the phone editor: scrim, grabber, kicker and headline, a
	44px close button. Closes on the scrim, on Escape and on a downward swipe
	of the grabber. Moved to <body> so glass parents cannot clip it.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { portal } from '$lib/editor/portal';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	interface Props {
		kicker?: string;
		title: string;
		onclose: () => void;
		/** the sheet takes most of the screen height */
		tall?: boolean;
		children: Snippet;
	}

	let { kicker, title, onclose, tall = false, children }: Props = $props();

	const id = `sheet-${Math.random().toString(36).slice(2, 8)}`;
	let panel: HTMLDivElement | undefined = $state();
	let drag_start: number | null = null;

	onMount(() => {
		const on_key = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onclose();
		};
		document.addEventListener('keydown', on_key);
		// the page behind must not scroll while the sheet is open
		const overflow = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		panel?.focus();
		return () => {
			document.removeEventListener('keydown', on_key);
			document.body.style.overflow = overflow;
		};
	});
</script>

<div use:portal class="sheet-root">
	<div
		class="scrim"
		role="presentation"
		onclick={onclose}
		transition:fade={{ duration: 150 }}
	></div>
	<div
		bind:this={panel}
		class="panel"
		class:panel-tall={tall}
		role="dialog"
		aria-modal="true"
		aria-labelledby={id}
		tabindex="-1"
		transition:fly={{ y: 320, duration: 220, opacity: 1 }}
	>
		<div
			class="grab-zone"
			role="presentation"
			ontouchstart={(e) => (drag_start = e.touches[0].clientY)}
			ontouchend={(e) => {
				if (drag_start !== null && e.changedTouches[0].clientY - drag_start > 60) onclose();
				drag_start = null;
			}}
		>
			<span class="grabber"></span>
		</div>
		<div class="head">
			<div class="min-w-0 flex-1">
				{#if kicker}
					<span class="bt-kicker kicker">{kicker}</span>
				{/if}
				<h2 {id} class="bt-headline headline">{title}</h2>
			</div>
			<button type="button" class="close" aria-label="Close" onclick={onclose}>
				<EdIcon name="x" size={20} />
			</button>
		</div>
		<div class="body">
			{@render children()}
		</div>
	</div>
</div>

<style>
	.sheet-root {
		position: fixed;
		inset: 0;
		z-index: 60;
	}
	.scrim {
		position: absolute;
		inset: 0;
		background: rgba(6, 4, 20, 0.62);
	}
	.panel {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
		max-height: calc(100dvh - max(24px, env(safe-area-inset-top)) - 24px);
		border-radius: 28px 28px 0 0;
		background: #1b1846;
		color: var(--ink);
		box-shadow: 0 -20px 60px rgba(0, 0, 0, 0.5);
		outline: none;
	}
	.panel-tall {
		height: calc(100dvh - max(24px, env(safe-area-inset-top)) - 24px);
	}
	.grab-zone {
		display: flex;
		justify-content: center;
		padding: 10px 0 12px;
	}
	.grabber {
		width: 40px;
		height: 5px;
		border-radius: 9px;
		background: rgba(255, 255, 255, 0.35);
	}
	.head {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		padding: 0 16px 14px;
	}
	.kicker {
		font-size: 13px;
		letter-spacing: 4px;
	}
	.headline {
		margin-top: 2px;
		font-size: 26px;
	}
	.close {
		display: grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
	}
	.close:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.body {
		min-height: 0;
		flex: 1;
		overflow-y: auto;
		overscroll-behavior: contain;
		padding: 0 16px calc(20px + env(safe-area-inset-bottom));
	}
</style>
