<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import '../app.css';
	import Navbar from '$lib/navbar.svelte';
	import { pathname } from '$lib/stores';
	import { navbarVisible } from '$lib/stores.svelte';

	import { initLocalizationContext } from '$lib/i18n';
	import { browser } from '$app/environment';
	import CommandPalette from '$lib/components/commandpalette.svelte';
	import { page } from '$app/state';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	if (browser) {
		pathname.set(window.location.pathname);
		// The app is dark only (Beauty Tech grounds).
		document.documentElement.classList.add('dark');
	}
	let start_language = 'en';
	const rtl_languages = ['he', 'prs', 'ps'];
	if (browser) {
		start_language = localStorage.getItem('language') ?? 'en';
		document.documentElement.lang = start_language;
		document.documentElement.dir = rtl_languages.includes(start_language) ? 'rtl' : 'ltr';
	}
	initLocalizationContext(start_language);
</script>

{#if navbarVisible.visible && page.url.pathname !== '/'}
	<Navbar />
	<div class="pt-16">
		<div class="z-40"></div>
	</div>
{/if}
{@render children?.()}
<CommandPalette />

<style>
	:global(#pips-slider) {
		--pip: #feffff;
		--pip-active: #feffff;
	}
</style>
