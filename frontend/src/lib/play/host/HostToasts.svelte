<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Small toasts for late joins during the game (bottom left of the stage). -->
<script lang="ts">
	import { fly } from 'svelte/transition';

	interface Props {
		items: { id: number; text: string }[];
	}

	let { items }: Props = $props();
</script>

<div class="ts" aria-live="polite">
	{#each items as item (item.id)}
		<div class="ts-item" in:fly={{ x: -40, duration: 300 }} out:fly={{ x: -40, duration: 300 }}>
			{item.text}
		</div>
	{/each}
</div>

<style>
	.ts {
		position: absolute;
		z-index: 20;
		left: 300px;
		bottom: 52px;
		display: flex;
		flex-direction: column-reverse;
		gap: 10px;
		pointer-events: none;
	}
	.ts-item {
		height: 52px;
		display: inline-flex;
		align-items: center;
		padding: 0 26px;
		border-radius: 9999px;
		background: var(--fill-deep);
		font-size: 22px;
		font-weight: 700;
		white-space: nowrap;
	}
</style>
