<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Top 5 after a question (midnight world with mesh): rank moves against the
	previous leaderboard, gradient bars, and "<NAME> TAKES THE LEAD" when the
	leader changes.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { flip } from 'svelte/animate';
	import { fly } from 'svelte/transition';
	import { fitText } from './fit';
	import { fmt, type LeaderboardData } from './worlds';

	interface Props {
		data: LeaderboardData;
		/** username to rank from the previous leaderboard, null on the first one */
		previous: Record<string, number> | null;
		total: number;
	}

	let { data, previous, total }: Props = $props();

	let grown = $state(false);
	onMount(() => {
		const id = setTimeout(() => (grown = true), 150);
		return () => clearTimeout(id);
	});

	const top = $derived(data.top.slice(0, 5));
	const best = $derived(Math.max(1, top[0]?.score ?? 1));
	const leader = $derived(top[0]?.username ?? '');
	const prevLeader = $derived.by(() => {
		if (!previous) return null;
		return Object.entries(previous).find(([, r]) => r === 1)?.[0] ?? null;
	});
	const headline = $derived(
		!leader
			? 'Nobody scored yet'
			: prevLeader && prevLeader === leader
				? `${leader} stays in front`
				: `${leader} takes the lead`
	);
	const move = (username: string, rank: number): { dir: 'up' | 'down' | 'flat'; n: number | null } => {
		if (!previous) return { dir: 'flat', n: null };
		const before = previous[username];
		if (before === undefined) return { dir: 'up', n: null };
		if (before > rank) return { dir: 'up', n: before - rank };
		if (before < rank) return { dir: 'down', n: rank - before };
		return { dir: 'flat', n: null };
	};
	const toGo = $derived(Math.max(0, total - (data.question_index + 1)));
</script>

<h1 class="h-title" style="right: 84px">
	<span class="h-kicker">Leaderboard after question {data.question_index + 1} of {total}</span>
	<span
		class="h-headline bt-text-aurora ld-headline"
		use:fitText={{ max: 72, min: 44, lines: 1, key: headline }}>{headline}</span
	>
</h1>

<div class="ld-rows">
	{#each top as entry, i (entry.username)}
		{@const m = move(entry.username, i + 1)}
		<div
			class="ld-row"
			class:ld-row--lead={i === 0}
			animate:flip={{ duration: 500 }}
			in:fly={{ x: -80, duration: 450, delay: 120 + (top.length - i) * 120 }}
		>
			<div class="ld-rank h-num">{i + 1}</div>
			<div class="ld-move ld-move--{m.dir}">
				{#if m.dir === 'up'}
					<svg viewBox="0 0 10 10" aria-label="Up"><path d="M5 1 L9.5 9 L0.5 9 Z" /></svg>{m.n ?? ''}
				{:else if m.dir === 'down'}
					<svg viewBox="0 0 10 10" aria-label="Down"><path d="M5 9 L9.5 1 L0.5 1 Z" /></svg>{m.n}
				{:else}
					<svg viewBox="0 0 10 10" aria-label="Same place"><rect x="1" y="4" width="8" height="2" /></svg>
				{/if}
			</div>
			<div class="ld-name">
				{entry.username}
				{#if entry.gained}<small>+{fmt(entry.gained)}</small>{/if}
			</div>
			<div class="ld-bar">
				<span style="width: {grown ? (entry.score / best) * 100 : 0}%"></span>
			</div>
			<div class="ld-pts h-num">{fmt(entry.score)}</div>
		</div>
	{:else}
		<p class="ld-empty">No scores yet.</p>
	{/each}
</div>

<div class="ld-foot">
	{data.total_players}
	{data.total_players === 1 ? 'player' : 'players'}, {toGo === 0
		? 'that was the last question'
		: `${toGo} ${toGo === 1 ? 'question' : 'questions'} to go`}
</div>

<style>
	.ld-headline {
		white-space: nowrap;
		overflow: hidden;
		padding-bottom: 4px;
	}
	.ld-rows {
		position: absolute;
		z-index: 3;
		left: 70px;
		right: 70px;
		top: 300px;
		display: flex;
		flex-direction: column;
		gap: 18px;
	}
	.ld-row {
		height: 120px;
		border-radius: 25px;
		background: var(--fill-card);
		display: grid;
		grid-template-columns: 120px 130px 640px 1fr 300px;
		align-items: center;
		padding: 0 44px 0 24px;
	}
	.ld-row--lead {
		background: radial-gradient(
			farthest-corner at 100% 100%,
			color-mix(in srgb, var(--accent-sky) 35%, transparent) 0%,
			color-mix(in srgb, var(--accent-blue) 38%, transparent) 48%,
			color-mix(in srgb, var(--accent-indigo) 60%, transparent) 100%
		);
	}
	.ld-rank {
		font-size: 88px;
		text-align: center;
	}
	.ld-move {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 28px;
		font-weight: 700;
	}
	.ld-move svg {
		width: 26px;
		height: 26px;
		fill: currentColor;
	}
	.ld-move--up {
		color: var(--accent-green-tint);
	}
	.ld-move--down {
		color: var(--accent-orchid-tint);
	}
	.ld-move--flat {
		color: var(--ink-muted);
	}
	.ld-name {
		font-size: 46px;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		padding-right: 24px;
	}
	.ld-name small {
		font-size: 24px;
		font-weight: 400;
		color: var(--ink-muted);
		margin-left: 10px;
	}
	.ld-bar {
		height: 18px;
		background: var(--fill-glass);
	}
	.ld-bar span {
		display: block;
		height: 100%;
		background: linear-gradient(90deg, var(--accent-blue) 0%, var(--accent-sky) 55%, var(--accent-green) 100%);
		transition: width 1000ms cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.ld-pts {
		font-size: 76px;
		text-align: right;
	}
	.ld-empty {
		font-size: 32px;
		color: var(--ink-muted);
	}
	.ld-foot {
		position: absolute;
		z-index: 3;
		left: 300px;
		right: 300px;
		top: 1000px;
		text-align: center;
		font-size: 22px;
		color: var(--ink-muted);
	}
</style>
