<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	let { quiz } = $props();
</script>

<a
	href="/view/{quiz.id}"
	class="bt-glass bt-glass-faint h-full flex flex-col gap-3 p-5 sm:p-6 hover:bg-white/[0.12] transition-colors"
>
	<h2 class="text-xl sm:text-2xl font-black leading-tight break-words line-clamp-2">
		{@html quiz.title}
	</h2>
	{#if quiz.description}
		<p class="text-sm text-ink-muted line-clamp-3 break-words">{@html quiz.description}</p>
	{/if}
	<p class="mt-auto pt-2 text-sm text-ink-muted">
		{$t('explore_page.made_by')}
		<span class="text-ink">{@html quiz.user}</span>
	</p>
</a>

<style>
	:global(mark) {
		background: rgba(93, 181, 223, 0.35);
		color: inherit;
		border-radius: 4px;
		padding: 0 2px;
	}
</style>
