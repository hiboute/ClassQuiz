<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone waiting screen once joined: "You're in", the nickname big, and a
	pointer to the big screen. Indigo world, like the lobby.
-->
<script lang="ts">
	import Logo from '$lib/brand/Logo.svelte';
	import PhoneShell from '$lib/play/phone/PhoneShell.svelte';
	import { plainText } from '$lib/play/phone/phone';

	interface Props {
		username: string;
		title?: string;
		description?: string;
		cover_image?: string | undefined;
		started?: boolean;
		total?: number | null;
	}

	let { username, title = '', started = false }: Props = $props();
	const quiz_title = $derived(plainText(title));
</script>

<PhoneShell world="indigo" mesh state="waiting">
	<Logo width={160} />
	<div class="pw-body" data-testid="waiting-screen">
		<span class="bt-eyebrow">{started ? 'Game in progress' : "You're in"}</span>
		<p class="pw-name bt-headline" class:pw-name-long={username.length > 12}>{username}</p>
		<p class="pw-look">
			<span class="bt-kicker">Look at</span>
			<span class="bt-headline pw-look-big">the big screen</span>
		</p>
		<p class="pw-sub">
			{started
				? 'You will play from the next question.'
				: 'The game starts when the host is ready.'}
		</p>
	</div>
	<div class="pw-foot">
		<span class="pw-dot" aria-hidden="true"></span>
		<span>{quiz_title || 'Live Quiz'}</span>
	</div>
</PhoneShell>

<style>
	.pw-body {
		margin: auto 0;
		padding: 40px 0;
	}
	.pw-name {
		margin: 14px 0 0;
		font-size: 52px;
		line-height: 1;
		text-transform: none;
		overflow-wrap: anywhere;
	}
	.pw-name-long {
		font-size: 40px;
	}
	.pw-look {
		margin: 44px 0 0;
	}
	.pw-look .bt-kicker {
		font-size: 20px;
	}
	.pw-look-big {
		font-size: 34px;
		margin-top: 4px;
	}
	.pw-sub {
		margin: 14px 0 0;
		font-size: 17px;
		color: var(--ink-muted);
	}
	.pw-foot {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 15px;
		color: var(--ink-muted);
	}
	.pw-dot {
		flex: none;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--accent-green);
		animation: pw-pulse 1.6s ease-in-out infinite;
	}
	@keyframes pw-pulse {
		50% {
			opacity: 0.3;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.pw-dot {
			animation: none;
		}
	}
</style>
