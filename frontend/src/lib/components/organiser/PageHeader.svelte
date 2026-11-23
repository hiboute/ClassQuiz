<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Organiser page title: tracked-capital eyebrow, Regular kicker over a Black
	headline, and an optional actions slot on the right (wraps under on phones).
-->
<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		eyebrow?: string;
		kicker?: string;
		headline: string;
		gradient?: boolean;
		class?: string;
		actions?: Snippet;
		children?: Snippet;
	}

	let {
		eyebrow,
		kicker,
		headline,
		gradient = false,
		class: klass = '',
		actions,
		children
	}: Props = $props();
</script>

<header class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between {klass}">
	<div class="min-w-0">
		{#if eyebrow}
			<span class="bt-eyebrow text-ink-muted mb-4">{eyebrow}</span>
		{/if}
		{#if kicker}
			<span class="bt-kicker text-lg lg:text-2xl">{kicker}</span>
		{/if}
		<h1
			class="bt-headline text-[32px] lg:text-[52px] break-words"
			class:bt-text-display={gradient}
		>
			{headline}
		</h1>
		{@render children?.()}
	</div>
	{#if actions}
		<div class="flex flex-wrap gap-3 shrink-0">
			{@render actions()}
		</div>
	{/if}
</header>
