<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import Footer from '$lib/footer.svelte';
	import World from '$lib/brand/World.svelte';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	navbarVisible.visible = true;
</script>

<World world="midnight" fullscreen={false} class="flex flex-col min-h-[calc(100dvh-4rem)]">
	<main class="flex-1 w-full max-w-3xl mx-auto px-4 pt-10 pb-6">
		<div class="bt-glass docs-card px-6 py-8 sm:px-10 sm:py-10">
			{@render children?.()}
		</div>
	</main>
	<Footer />
</World>

<style>
	.docs-card :global(article) {
		max-width: none;
	}
	.docs-card :global(.prose) {
		--tw-prose-body: var(--ink-muted);
		--tw-prose-headings: var(--ink);
		--tw-prose-links: var(--ink);
		--tw-prose-bold: var(--ink);
		--tw-prose-bullets: var(--ink-muted);
		--tw-prose-th-borders: rgba(254, 255, 255, 0.25);
		--tw-prose-td-borders: rgba(254, 255, 255, 0.12);
	}
	.docs-card :global(.prose h1) {
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}
	.docs-card :global(.prose a) {
		text-underline-offset: 4px;
	}
</style>
