<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone result after each question: correct or wrong, the points of the
	round, the player's rank (from rank_update) and the total and streak
	tiles. Keeps the question's colour world. The rank card keeps its size
	while rank_update is on its way, so nothing jumps.
-->
<script lang="ts">
	import Logo from '$lib/brand/Logo.svelte';
	import ShapeMark from '$lib/brand/ShapeMark.svelte';
	import { answerStyle } from '$lib/brand/answers';
	import PhoneShell from './PhoneShell.svelte';
	import {
		formatPoints,
		ordinal,
		ordinalSuffix,
		questionWorld,
		type LockedAnswer,
		type OwnResult,
		type RankUpdate
	} from './phone';

	interface Props {
		question_index: number;
		question_type?: string;
		/** this player's row of question_results, or null when they did not answer */
		own: OwnResult | null;
		rank?: RankUpdate | null;
		/** rank after the previous question, to say "Up 5 places" */
		prev_rank?: number | null;
		/** what the player picked, as shown when locked */
		locked?: LockedAnswer | null;
		/** total before this question, used until rank_update arrives */
		fallback_total?: number | null;
	}

	let {
		question_index,
		question_type = 'ABCD',
		own,
		rank = null,
		prev_rank = null,
		locked = null,
		fallback_total = null
	}: Props = $props();

	const type = $derived(String(question_type).toUpperCase());
	const graded = $derived(!['VOTING', 'SLIDE', 'WORD_CLOUD'].includes(type));
	const answered = $derived(own !== null);
	const right = $derived(Boolean(own?.right));
	const gained = $derived(Math.max(0, Math.round(rank?.gained ?? own?.score ?? 0)));
	const bonus = $derived(Math.round(own?.streak_bonus ?? 0));
	const seconds = $derived(own ? Math.max(0, own.time_taken / 1000) : null);
	const streak = $derived(rank?.streak ?? own?.streak ?? 0);
	const total = $derived(rank?.total ?? (fallback_total ?? 0) + (own?.score ?? 0));

	const kicker = $derived(
		locked?.label ? `${locked.label}.` : answered ? `${own?.answer}.` : 'No answer.'
	);
	const headline = $derived(
		!graded ? (answered ? 'Vote counted.' : 'No vote.') : !answered ? 'Time is up.' : right ? 'Correct.' : 'Wrong.'
	);
	const chip_index = $derived(locked?.index);

	const movement = $derived.by(() => {
		if (!rank) return '';
		if (rank.rank === 1) {
			return rank.total_players > 1 ? 'You lead' : 'You lead, all alone';
		}
		const parts: string[] = [];
		if (prev_rank !== null && prev_rank !== undefined) {
			const d = prev_rank - rank.rank;
			if (d > 0) parts.push(`Up ${d} place${d === 1 ? '' : 's'}`);
			else if (d < 0) parts.push(`Down ${-d} place${d === -1 ? '' : 's'}`);
			else parts.push('Same place');
		}
		if (rank.behind_gap !== null && rank.behind_gap !== undefined && rank.behind_username) {
			parts.push(
				`${formatPoints(rank.behind_gap)} point${rank.behind_gap === 1 ? '' : 's'} behind ${rank.behind_username}`
			);
		} else if (rank.rank > 1) {
			parts.push(`${ordinal(rank.rank - 1)} is in reach`);
		}
		return parts.join(', ');
	});
</script>

<PhoneShell world={questionWorld(question_index)} state="result">
	<div class="pr-head" data-testid="result-screen" data-result={graded ? (right ? 'right' : answered ? 'wrong' : 'none') : 'vote'}>
		{#if chip_index !== undefined}
			{@const st = answerStyle(chip_index)}
			<span class="pr-chip {st.className}" aria-hidden="true">
				<ShapeMark index={chip_index} size={40} />
			</span>
		{/if}
		<div class="pr-status">
			<span class="bt-kicker pr-kicker">{kicker}</span>
			<span class="bt-headline pr-headline" class:bt-text-aurora={graded && right}>{headline}</span>
		</div>
	</div>

	{#if graded}
		<div class="pr-points">
			<div class="pr-num bt-num" data-testid="result-points">+{formatPoints(gained)}</div>
			<p>
				{#if seconds !== null}
					Points this round, answered in {seconds.toFixed(1)} s
				{:else}
					No points this round
				{/if}
			</p>
			<p class="pr-bonus">
				{#if bonus > 0}Includes a +{formatPoints(bonus)} streak bonus{:else}&nbsp;{/if}
			</p>
		</div>
	{:else}
		<div class="pr-points pr-points-quiet">
			<p>No points on this one. See what the room said on the big screen.</p>
		</div>
	{/if}

	<div class="pr-rank bt-glass-deep" data-testid="rank-card">
		<span class="bt-eyebrow pr-label">Your rank</span>
		{#if rank}
			<div class="pr-rank-num bt-num">{rank.rank}<sup>{ordinalSuffix(rank.rank)}</sup></div>
			<div class="pr-rank-of">of {formatPoints(rank.total_players)} players</div>
			<div class="pr-rank-gap">{movement || ' '}</div>
		{:else}
			<div class="pr-rank-num bt-num" aria-hidden="true"><span class="pr-wait"></span></div>
			<div class="pr-rank-of">Counting the scores</div>
			<div class="pr-rank-gap">&nbsp;</div>
		{/if}
	</div>

	<div class="pr-stats">
		<div class="pr-tile bt-glass-faint">
			<b class="bt-num">{formatPoints(total)}</b>Total score
		</div>
		<div class="pr-tile bt-glass-faint">
			<b class="bt-num">{streak}</b>Answer streak
			{#if streak >= 2}
				<span class="pr-streak">Streak x{streak}</span>
			{/if}
		</div>
	</div>

	<div class="pr-foot">
		<Logo width={160} />
		<span>Next question soon</span>
	</div>
</PhoneShell>

<style>
	.pr-head {
		display: flex;
		align-items: center;
		gap: 16px;
		min-height: 72px;
	}
	.pr-chip {
		flex: none;
		width: 72px;
		height: 72px;
		justify-content: center;
		border-radius: var(--radius-bt-lg);
	}
	.pr-status {
		min-width: 0;
	}
	.pr-kicker {
		font-size: 18px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.pr-headline {
		font-size: 44px;
	}
	.pr-points {
		margin-top: 44px;
		text-align: center;
	}
	.pr-num {
		font-size: 124px;
		line-height: 0.9;
	}
	.pr-points p {
		margin: 14px 0 0;
		font-size: 18px;
		color: var(--ink-muted);
	}
	.pr-points .pr-bonus {
		margin-top: 6px;
		font-size: 15px;
		color: var(--accent-green-tint);
	}
	.pr-points-quiet {
		margin-top: 32px;
		text-align: left;
	}
	.pr-rank {
		margin-top: 36px;
		border-radius: var(--radius-bt-xl);
		padding: 22px 20px 20px;
		text-align: center;
	}
	.pr-label {
		color: var(--ink-muted);
	}
	.pr-rank-num {
		margin-top: 12px;
		font-size: 84px;
		min-height: 71px;
	}
	.pr-rank-num sup {
		font-size: 34px;
		vertical-align: top;
		position: relative;
		top: 4px;
		margin-left: 2px;
	}
	.pr-wait {
		display: inline-block;
		width: 96px;
		height: 60px;
		border-radius: var(--radius-bt-md);
		background: var(--fill-glass-mid);
		animation: pr-pulse 1.2s ease-in-out infinite;
	}
	@keyframes pr-pulse {
		50% {
			opacity: 0.4;
		}
	}
	.pr-rank-of {
		margin-top: 10px;
		font-size: 20px;
	}
	.pr-rank-gap {
		margin-top: 14px;
		min-height: 38px;
		font-size: 16px;
		line-height: 19px;
		color: var(--accent-green-tint);
	}
	.pr-stats {
		margin-top: 12px;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
	}
	.pr-tile {
		position: relative;
		border-radius: var(--radius-bt-xl);
		padding: 16px 12px;
		font-size: 15px;
		color: var(--ink-muted);
		text-align: center;
	}
	.pr-tile b {
		display: block;
		margin-bottom: 6px;
		font-size: 34px;
		line-height: 0.9;
		color: var(--ink);
	}
	.pr-streak {
		position: absolute;
		top: -9px;
		right: 10px;
		padding: 3px 10px;
		border-radius: 9999px;
		background: linear-gradient(120deg, var(--accent-pink), var(--accent-orchid));
		color: var(--ink-dark);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 1.5px;
		text-transform: uppercase;
	}
	@media (max-height: 760px) {
		.pr-points {
			margin-top: 24px;
		}
		.pr-num {
			font-size: 100px;
		}
		.pr-rank {
			margin-top: 20px;
			padding: 16px 16px 14px;
		}
		.pr-rank-num {
			font-size: 70px;
			min-height: 59px;
		}
	}
	.pr-foot {
		margin-top: auto;
		padding-top: 20px;
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 12px;
	}
	.pr-foot span {
		font-size: 14px;
		color: var(--ink-muted);
	}
</style>
