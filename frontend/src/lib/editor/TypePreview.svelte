<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- The little picture of a question type, drawn inside a dark preview box. -->
<script lang="ts">
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import type { TypePreviewKind } from '$lib/editor/editor_meta';

	let { kind }: { kind: TypePreviewKind } = $props();
</script>

{#if kind === 'tiles' || kind === 'check'}
	<span class="grid w-full grid-cols-2 gap-1">
		{#each [0, 1, 2, 3] as k}
			<span class="pv-tile bt-tile-{['a', 'b', 'c', 'd'][k]}">
				<ShapeMark index={k} size={10} />
				{#if kind === 'check' && k < 2}
					<EdIcon name="check" size={11} stroke={3} class="ml-auto" />
				{/if}
			</span>
		{/each}
	</span>
{:else if kind === 'truefalse'}
	<span class="grid w-full grid-cols-2 gap-1">
		<span class="pv-tile pv-tall bt-tile-a"><ShapeMark index={0} size={11} />True</span>
		<span class="pv-tile pv-tall bt-tile-b"><ShapeMark index={1} size={11} />False</span>
	</span>
{:else if kind === 'cloud'}
	<span class="cloud">
		<b class="text-[19px] text-accent-sky">beauty</b>
		<b class="text-[12px] text-accent-pink">AI</b>
		<b class="text-[14px] text-accent-green">skin</b>
		<b class="text-[11px]">data</b>
		<b class="text-[15px] text-accent-orchid">care</b>
	</span>
{:else if kind === 'poll'}
	<span class="flex h-full w-full items-end justify-center gap-1.5">
		{#each [55, 85, 35, 65] as h, k}
			<span class="pv-bar bt-tile-{['a', 'b', 'c', 'd'][k]}" style="height:{h}%"></span>
		{/each}
	</span>
{:else if kind === 'order'}
	<span class="flex w-full flex-col gap-1">
		{#each [1, 2, 3] as n}
			<span class="pv-line"><b class="bt-num">{n}</b><i></i></span>
		{/each}
	</span>
{:else if kind === 'text'}
	<span class="pv-input">Type here<i></i></span>
{:else if kind === 'range'}
	<span class="pv-range"><i></i><b></b></span>
{/if}

<style>
	.pv-tile {
		display: flex;
		align-items: center;
		gap: 6px;
		height: 24px;
		padding: 0 8px;
		border-radius: 7px;
		font-size: 11px;
	}
	.pv-tall {
		height: 52px;
		justify-content: center;
		letter-spacing: 1px;
	}
	.cloud {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: center;
		gap: 2px 8px;
		line-height: 1;
	}
	.pv-bar {
		width: 16%;
		border-radius: 5px 5px 2px 2px;
	}
	.pv-line {
		display: flex;
		align-items: center;
		gap: 8px;
		height: 16px;
		padding: 0 8px;
		border-radius: 6px;
		background: var(--fill-glass-mid);
		font-size: 11px;
	}
	.pv-line i {
		flex: 1;
		height: 3px;
		border-radius: 2px;
		background: var(--fill-glass-strong);
	}
	.pv-input {
		display: flex;
		align-items: center;
		width: 100%;
		height: 34px;
		padding: 0 12px;
		border-radius: 12px;
		background: var(--fill-glass-mid);
		font-size: 12px;
		color: var(--ink-muted);
	}
	.pv-input i {
		width: 2px;
		height: 16px;
		margin-left: 3px;
		background: var(--accent-sky);
	}
	.pv-range {
		position: relative;
		width: 100%;
		height: 6px;
		border-radius: 3px;
		background: var(--fill-glass-strong);
	}
	.pv-range i {
		position: absolute;
		left: 30%;
		right: 30%;
		top: 0;
		bottom: 0;
		border-radius: 3px;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
	}
	.pv-range b {
		position: absolute;
		left: 30%;
		top: -6px;
		width: 18px;
		height: 18px;
		border-radius: 999px;
		background: var(--ink);
	}
</style>
