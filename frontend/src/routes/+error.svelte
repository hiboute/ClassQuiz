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
		headline="Page not found"
		message="This page does not exist, or it moved. Check the address, or head back to a game."
	/>
{:else}
	<ErrorPanel
		{status}
		headline="Something went wrong"
		message="The server could not finish this request. Try again in a moment."
	/>
{/if}
