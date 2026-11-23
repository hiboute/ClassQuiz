<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { page } from '$app/state';
	import ErrorPanel from '$lib/components/organiser/ErrorPanel.svelte';

	navbarVisible.visible = true;
	const status = $derived(page.status);
</script>

{#if status === 404}
	<ErrorPanel
		{status}
		headline="Quiz not found"
		message="This quiz was deleted, made private, or never existed."
	/>
{:else}
	<ErrorPanel
		{status}
		headline="Something went wrong"
		message="The quiz could not be loaded. Try again in a moment."
	/>
{/if}
