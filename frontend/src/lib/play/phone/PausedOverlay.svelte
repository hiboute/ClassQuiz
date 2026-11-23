<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Full-screen "Paused" layer over the current phone screen while the host pauses. -->
<script lang="ts">
	interface Props {
		remaining?: number | null;
	}
	let { remaining = null }: Props = $props();
</script>

<div class="pp" role="alertdialog" aria-modal="true" aria-label="Game paused" data-testid="paused">
	<div class="pp-card">
		<span class="bt-eyebrow">Hold on</span>
		<span class="bt-headline pp-headline">Paused</span>
		<p class="pp-sub">
			The host paused the game.{#if remaining !== null && remaining !== undefined}
				{' '}{Math.ceil(remaining)} s left when it resumes.{/if}
		</p>
	</div>
</div>

<style>
	.pp {
		position: fixed;
		inset: 0;
		z-index: 50;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px max(20px, env(safe-area-inset-right)) 24px max(20px, env(safe-area-inset-left));
		background: rgba(9, 9, 36, 0.72);
		-webkit-backdrop-filter: blur(10px);
		backdrop-filter: blur(10px);
		color: var(--ink);
		touch-action: none;
	}
	.pp-card {
		width: 100%;
		max-width: 420px;
		padding: 28px 24px 26px;
		border-radius: var(--radius-bt-xl);
		background: var(--fill-deep);
	}
	.pp-headline {
		margin-top: 8px;
		font-size: 52px;
	}
	.pp-sub {
		margin: 12px 0 0;
		font-size: 17px;
		color: var(--ink-muted);
	}
</style>
