<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Shown when the host removes the player from the game. -->
<script lang="ts">
	import Logo from '$lib/brand/Logo.svelte';
	import PhoneShell from './PhoneShell.svelte';
</script>

<PhoneShell world="midnight" state="kicked">
	<Logo width={160} />
	<div class="pk" data-testid="kicked">
		<span class="bt-kicker pk-kicker">The host removed you</span>
		<span class="bt-headline pk-headline">from this game</span>
		<p class="pk-sub">
			You can no longer answer in this game. If this was a mistake, talk to the host.
		</p>
	</div>
	<a class="bt-btn-ghost bt-btn-lg bt-btn-block" href="/">Back to the start</a>
</PhoneShell>

<style>
	.pk {
		margin: auto 0;
		padding: 32px 0;
	}
	.pk-kicker {
		font-size: 20px;
	}
	.pk-headline {
		margin-top: 4px;
		font-size: 40px;
	}
	.pk-sub {
		margin: 16px 0 0;
		font-size: 17px;
		color: var(--ink-muted);
	}
</style>
