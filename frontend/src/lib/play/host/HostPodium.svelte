<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Final podium (ultraviolet world): builds 3rd, 2nd, then 1st, with names and
	points. `actions` holds the host's export and full-results buttons.
-->
<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import confetti from 'canvas-confetti';
	import { fitText } from './fit';
	import { fmt, type PodiumData } from './worlds';
	import { hostSound } from './sound.svelte';

	interface Props {
		data: PodiumData;
		quizTitle?: string;
		/** right answers per player, when known */
		rights?: Record<string, number> | null;
		questionCount?: number;
		/** show everything at once (demo screenshots) */
		instant?: boolean;
		actions?: Snippet;
	}

	let { data, quizTitle = '', rights = null, questionCount = 0, instant = false, actions }: Props =
		$props();

	let step = $state(0);

	onMount(() => {
		if (instant) {
			step = 3;
			return;
		}
		const has = (r: number) => data.top.some((t) => t.rank === r);
		const timers = [
			setTimeout(() => {
				step = 1;
				if (has(3)) hostSound.podium(3);
			}, 700),
			setTimeout(() => {
				step = 2;
				if (has(2)) hostSound.podium(2);
			}, 2200),
			setTimeout(() => {
				step = 3;
				hostSound.podium(1);
				try {
					const colors = ['#5db5df', '#27be82', '#d783ff', '#f982fa', '#a59fff'];
					confetti({ particleCount: 160, spread: 100, origin: { y: 0.55 }, colors });
					setTimeout(
						() => confetti({ particleCount: 120, spread: 140, origin: { y: 0.5 }, colors }),
						500
					);
				} catch {
					/* no canvas: skip */
				}
			}, 3900)
		];
		return () => timers.forEach(clearTimeout);
	});

	const byRank = (r: number) => data.top.find((t) => t.rank === r) ?? null;
	const initials = (name: string) =>
		name
			.split(/\s+/)
			.filter(Boolean)
			.slice(0, 2)
			.map((p) => [...p][0]?.toUpperCase() ?? '')
			.join('');
	const winner = $derived(byRank(1));
	const headline = $derived(winner ? `${winner.username} wins` : 'Final results');
	const shownAt: Record<number, number> = { 3: 1, 2: 2, 1: 3 };
</script>

<h1 class="pd-title">
	<span class="h-kicker">{quizTitle ? `${quizTitle}, ` : ''}final results</span>
	{#if step >= 3}
		<span
			class="h-headline bt-text-display pd-headline"
			in:fade={{ duration: 500 }}
			use:fitText={{ max: 80, min: 48, lines: 1, key: headline }}>{headline}</span
		>
	{:else}
		<span class="h-headline pd-headline pd-headline--wait">And the podium is</span>
	{/if}
</h1>

<div class="pd-stage">
	{#each [2, 1, 3] as rank}
		{@const p = byRank(rank)}
		<div class="pd-col pd-col--{rank}">
			{#if step >= shownAt[rank]}
				{#if p}
					<div class="pd-who" in:fly={{ y: 40, duration: 500, delay: 250 }}>
						<div class="pd-avatar">{initials(p.username)}</div>
						<div class="pd-name">{p.username}</div>
						<div class="pd-pts">
							<b>{fmt(p.score)}</b> points{#if rights && rights[p.username] !== undefined && questionCount},
								{rights[p.username]} of {questionCount} right{/if}
						</div>
					</div>
				{/if}
				<div class="pd-block pd-block--{rank}" in:fly={{ y: 400, duration: 600 }}>
					<span class="h-num">{rank}</span>
				</div>
			{/if}
		</div>
	{/each}
</div>

{#if actions && step >= 3}
	<div class="pd-actions" in:fade={{ delay: 600 }}>{@render actions()}</div>
{/if}

<style>
	.pd-title {
		position: absolute;
		z-index: 3;
		left: 0;
		right: 0;
		top: 81px;
		margin: 0;
		text-align: center;
		text-transform: uppercase;
	}
	.pd-headline {
		font-size: 80px;
		margin: 8px auto 0;
		width: 1700px;
		white-space: nowrap;
		overflow: hidden;
		padding-bottom: 4px;
	}
	.pd-headline--wait {
		color: var(--ink-muted);
		font-size: 64px;
	}
	.pd-stage {
		position: absolute;
		z-index: 3;
		left: 0;
		right: 0;
		bottom: 120px;
		display: flex;
		justify-content: center;
		align-items: flex-end;
		gap: 28px;
	}
	.pd-col {
		width: 440px;
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
	}
	.pd-who {
		margin-bottom: 26px;
		width: 100%;
	}
	.pd-avatar {
		width: 112px;
		height: 112px;
		margin: 0 auto 18px;
		border-radius: 9999px;
		background: var(--fill-glass-strong);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 40px;
		font-weight: 900;
	}
	.pd-name {
		font-size: 44px;
		font-weight: 900;
		text-transform: uppercase;
		line-height: 1.08;
		overflow-wrap: anywhere;
	}
	.pd-pts {
		margin-top: 10px;
		font-size: 28px;
		color: var(--ink-muted);
	}
	.pd-pts b {
		color: var(--ink);
		font-weight: 700;
	}
	.pd-block {
		width: 100%;
		display: flex;
		justify-content: center;
		padding-top: 28px;
	}
	.pd-block .h-num {
		font-size: 180px;
	}
	.pd-block--1 {
		height: 380px;
		background: linear-gradient(180deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		color: var(--ink-dark);
	}
	.pd-block--2 {
		height: 280px;
		background: linear-gradient(180deg, var(--accent-orchid) 0%, var(--accent-pink) 100%);
		color: var(--ink-dark);
	}
	.pd-block--3 {
		height: 200px;
		background: linear-gradient(180deg, var(--accent-violet) 0%, var(--accent-purple) 100%);
	}
	.pd-block--3 .h-num {
		font-size: 140px;
	}
	.pd-col--1 .pd-avatar {
		width: 140px;
		height: 140px;
		font-size: 50px;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
		color: var(--ink-dark);
	}
	.pd-col--1 .pd-name {
		font-size: 56px;
	}
	.pd-actions {
		position: absolute;
		z-index: 6;
		left: 50%;
		transform: translateX(-50%);
		top: 984px;
		display: flex;
		gap: 12px;
	}
</style>
