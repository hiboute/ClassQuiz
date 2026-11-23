<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Orchid chip in the phone top bar: warning icon and the number of problems. -->
<script lang="ts">
	import EdIcon from '$lib/editor/EdIcon.svelte';

	let { count, onclick }: { count: number; onclick: () => void } = $props();
</script>

<button
	type="button"
	class="pchip"
	aria-label="{count} {count === 1 ? 'problem' : 'problems'}, show the next one"
	{onclick}
>
	<EdIcon name="warn" size={17} />
	<span class="tabular-nums">{count}</span>
</button>

<style>
	.pchip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		flex: none;
		height: 44px;
		min-width: 44px;
		padding: 0 14px;
		border-radius: 999px;
		background: rgba(215, 131, 255, 0.24);
		color: var(--accent-orchid-tint);
		font-size: 15px;
		font-weight: 900;
	}
	.pchip:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
</style>
