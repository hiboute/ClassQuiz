<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone end screen, from the `podium` payload: the player's final rank big,
	their total, and the top 3. A quiet glow celebrates a podium finish.
	Ultraviolet world, like the podium on the big screen.
-->
<script lang="ts">
	import Logo from '$lib/brand/Logo.svelte';
	import PhoneShell from '$lib/play/phone/PhoneShell.svelte';
	import { formatPoints, ordinalSuffix, type PodiumData } from '$lib/play/phone/phone';

	interface Props {
		podium: PodiumData | null;
		username: string;
		/** total known on the phone, used while the podium is on its way */
		fallback_total?: number | null;
	}

	let { podium, username, fallback_total = null }: Props = $props();

	const rank = $derived(podium?.rank ?? null);
	const total = $derived(podium?.total ?? fallback_total ?? 0);
	const on_podium = $derived(rank !== null && rank >= 1 && rank <= 3);
	const kicker = $derived(
		rank === 1 ? 'Winner' : on_podium ? 'On the podium' : rank !== null ? 'You finished' : 'Game over'
	);
</script>

<PhoneShell world="ultraviolet" mesh state="end">
	<Logo width={160} />

	<div class="pe-main" data-testid="end-screen">
		<span class="bt-eyebrow">Final results</span>
		{#if podium === null}
			<p class="pe-wait">
				<span class="bt-kicker pe-kicker">Thanks for playing</span>
				<span class="bt-headline pe-headline">Look at the big screen</span>
			</p>
		{:else}
			<div class="pe-rank" class:pe-glow={on_podium}>
				<span class="bt-kicker pe-kicker">{kicker}</span>
				{#if rank !== null}
					<div class="pe-num bt-num">
						<span class:bt-text-aurora={on_podium}>{rank}</span><sup
							class:bt-text-aurora={on_podium}>{ordinalSuffix(rank)}</sup
						>
					</div>
					<div class="pe-of">of {formatPoints(podium.total_players)} players</div>
				{/if}
				<div class="pe-total">
					<b class="bt-num">{formatPoints(total)}</b> points
				</div>
			</div>

			{#if podium.top.length}
				<ol class="pe-top" aria-label="Top 3">
					{#each podium.top as row (row.rank)}
						<li class="pe-row" class:pe-me={row.username === username}>
							<span class="pe-row-rank bt-num">{row.rank}</span>
							<span class="pe-row-name">{row.username}</span>
							<span class="pe-row-score bt-num">{formatPoints(row.score)}</span>
						</li>
					{/each}
				</ol>
			{/if}
		{/if}
	</div>

	<p class="pe-foot">Thanks for playing, {username}.</p>
</PhoneShell>

<style>
	.pe-main {
		margin: auto 0;
		padding: 28px 0;
	}
	.pe-rank {
		position: relative;
		margin-top: 14px;
	}
	.pe-glow::before {
		content: '';
		position: absolute;
		z-index: -1;
		left: -40px;
		top: -10px;
		width: 280px;
		height: 220px;
		border-radius: 50%;
		background: radial-gradient(
			closest-side,
			rgba(93, 181, 223, 0.45),
			rgba(39, 190, 130, 0.18) 60%,
			transparent
		);
		filter: blur(8px);
		animation: pe-breathe 3.2s ease-in-out infinite;
	}
	@keyframes pe-breathe {
		50% {
			opacity: 0.55;
			transform: scale(1.06);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.pe-glow::before {
			animation: none;
		}
	}
	.pe-kicker {
		font-size: 20px;
	}
	.pe-num {
		display: flex;
		align-items: flex-start;
		margin-top: 14px;
		font-size: 140px;
		line-height: 0.86;
	}
	.pe-num sup {
		font-size: 48px;
		line-height: 1;
		margin-left: 4px;
		vertical-align: baseline;
		position: static;
	}
	.pe-of {
		margin-top: 12px;
		font-size: 20px;
	}
	.pe-total {
		margin-top: 18px;
		font-size: 18px;
		color: var(--ink-muted);
	}
	.pe-total b {
		font-size: 34px;
		color: var(--ink);
	}
	.pe-wait {
		margin: 14px 0 0;
	}
	.pe-headline {
		font-size: 40px;
		margin-top: 4px;
	}
	.pe-top {
		list-style: none;
		margin: 32px 0 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.pe-row {
		display: flex;
		align-items: center;
		gap: 14px;
		min-height: 60px;
		padding: 0 18px 0 14px;
		border-radius: var(--radius-bt-xl);
		background: var(--fill-glass);
	}
	.pe-me {
		background: var(--fill-glass-strong);
	}
	.pe-row-rank {
		flex: none;
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-bt-md);
		background: var(--fill-deep);
		font-size: 20px;
		line-height: 1;
	}
	.pe-row-name {
		flex: 1 1 auto;
		min-width: 0;
		font-size: 18px;
		font-weight: 700;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.pe-row-score {
		flex: none;
		font-size: 20px;
		line-height: 1;
	}
	.pe-foot {
		margin: 0;
		font-size: 15px;
		color: var(--ink-muted);
	}
</style>
