<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Organiser dialog: dimmed backdrop, a deep glass panel in the given world,
	closes on backdrop click and Escape.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import type { World } from '$lib/brand/answers';

	interface Props {
		open?: boolean;
		world?: World;
		label: string;
		wide?: boolean;
		onclose?: () => void;
		children?: Snippet;
	}

	let { open = true, world = 'indigo', label, wide = false, onclose, children }: Props = $props();

	const onkeydown = (e: KeyboardEvent) => {
		if (open && e.key === 'Escape') onclose?.();
	};
</script>

<svelte:window {onkeydown} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-[#05040f]/70 backdrop-blur-sm sm:p-6"
		transition:fade={{ duration: 120 }}
		onclick={(e) => {
			if (e.target === e.currentTarget) onclose?.();
		}}
		role="presentation"
	>
		<div
			data-world={world}
			role="dialog"
			aria-modal="true"
			aria-label={label}
			class="bt-world-ground relative w-full max-h-[92dvh] overflow-y-auto rounded-t-[25px] sm:rounded-[25px] shadow-2xl {wide
				? 'sm:max-w-3xl'
				: 'sm:max-w-xl'}"
			transition:fly={{ y: 24, duration: 180 }}
		>
			<button
				type="button"
				class="absolute top-4 end-4 z-10 h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-ink"
				aria-label="Close"
				onclick={() => onclose?.()}
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
					><path stroke-linecap="round" d="M6 6l12 12M18 6L6 18" /></svg
				>
			</button>
			{@render children?.()}
		</div>
	</div>
{/if}
