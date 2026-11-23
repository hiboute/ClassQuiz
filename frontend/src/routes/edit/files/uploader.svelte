<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import Loading from '$lib/editor/Loading.svelte';
	import type { EditorData } from '$lib/quiz_types';

	let uppyOpen = $state(false);
	let data = $state({ cover_image: undefined } as EditorData);

	$effect(() => {
		if (data.cover_image) {
			window.location.reload();
		}
	});
</script>

{#await import('$lib/editor/uploader.svelte')}
	<Loading />
{:then c}
	<c.default
		bind:modalOpen={uppyOpen}
		bind:data
		video_upload={true}
		library_enabled={false}
	/>
{/await}
