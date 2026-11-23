<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	let { data } = $props();
	const error = $derived(data.error);
</script>

<main class="min-h-[calc(100dvh-4rem)] flex items-center justify-center px-4 py-10">
	<div class="bt-glass w-full max-w-lg p-6 sm:p-10">
		<span class="bt-eyebrow text-ink-muted mb-3">Sign in</span>
		<h1 class="bt-headline text-[28px] sm:text-[38px]">Sign in did not work</h1>
		<p class="mt-4 text-ink-muted">
			{#if error === 'email'}
				The provider did not share an email address. Check that the email on that account is
				verified, then try again.
			{:else}
				The provider could not confirm who you are. Check that your account has a verified email,
				then try again.
			{/if}
		</p>
		<a href="/account/login" class="bt-btn-primary mt-8">Back to sign in</a>
	</div>
</main>
