<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Small floating pill while the socket is reconnecting. Positioned over the
	screen (no layout shift), under the safe-area top inset.
-->
<script lang="ts">
	interface Props {
		visible: boolean;
	}
	let { visible }: Props = $props();
</script>

{#if visible}
	<div class="pc" role="status" aria-live="polite" data-testid="reconnecting">
		<span class="pc-dot" aria-hidden="true"></span>
		Reconnecting. Your game is kept.
	</div>
{/if}

<style>
	.pc {
		position: fixed;
		z-index: 60;
		left: 50%;
		top: max(10px, calc(env(safe-area-inset-top) + 6px));
		transform: translateX(-50%);
		display: inline-flex;
		align-items: center;
		gap: 10px;
		max-width: calc(100vw - 32px);
		padding: 10px 16px;
		border-radius: 9999px;
		background: var(--fill-deep);
		-webkit-backdrop-filter: blur(12px);
		backdrop-filter: blur(12px);
		color: var(--ink);
		font-size: 14px;
		white-space: nowrap;
		pointer-events: none;
	}
	.pc-dot {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		background: var(--accent-orchid);
		animation: pc-blink 1s ease-in-out infinite;
	}
	@keyframes pc-blink {
		50% {
			opacity: 0.25;
		}
	}
</style>
