<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { page } from '$app/state';
	import { getLocalization } from '$lib/i18n';

	navbarVisible.visible = true;
	let status = page.status;
	const { t } = getLocalization();
</script>

<svelte:head>
	<title>{$t('words.error')} - {status}</title>
</svelte:head>
<div class="bt-glass max-w-xl mx-4 sm:mx-auto mt-16 px-8 py-10 text-center">
	<span class="bt-eyebrow text-ink-muted">Live Quiz</span>
	<h1 class="mt-3 text-7xl font-black bt-num">{status}</h1>
	<p class="mt-4 text-ink-muted">
		{#if status === 404}
			{$t('error_page.404_text')}
		{:else if status === 410}
			{$t('quiztivity.share_expired')}
		{:else}
			{$t('error_page.unknown_error_text')}
		{/if}
	</p>
	<a href="/" class="bt-btn-ghost mt-8">Home</a>
</div>
