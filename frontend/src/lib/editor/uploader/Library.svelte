<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PrivateImageData } from '$lib/quiz_types';
	import type { EditorData } from '$lib/quiz_types';
	import Loading from '$lib/editor/Loading.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import { getLocalization } from '$lib/i18n';

	interface Props {
		data: EditorData;
		selected_question: number;
		modalOpen: boolean;
	}

	let { data = $bindable(), selected_question, modalOpen = $bindable() }: Props = $props();

	const { t } = getLocalization();

	const fetch_images = async (): Promise<PrivateImageData[]> => {
		const response = await fetch('/api/v1/storage/list/last?count=50');
		return await response.json();
	};
	let image_fetch = fetch_images();

	const set_image = (id: string) => {
		if (selected_question === undefined) {
			data.cover_image = id;
		} else if (selected_question === -1) {
			data.background_image = id;
		} else {
			data.questions[selected_question].image = id;
		}
		modalOpen = false;
	};
</script>

<div
	class="bt-glass panel flex max-h-[85dvh] w-full max-w-4xl flex-col p-6"
	role="dialog"
	aria-modal="true"
	aria-labelledby="library-title"
>
	<div class="mb-4 flex items-start gap-4">
		<div class="flex-1">
			<span class="bt-eyebrow text-[11px] text-ink-muted">Media</span>
			<h2 id="library-title" class="bt-headline text-2xl">{$t('words.library')}</h2>
		</div>
		<button type="button" class="close" aria-label="Close" onclick={() => (modalOpen = false)}
			><EdIcon name="x" size={20} /></button
		>
	</div>
	{#await image_fetch}
		<Loading />
	{:then images}
		{#if images.length === 0}
			<p class="py-10 text-center text-ink-muted">No images yet. Upload one first.</p>
		{/if}
		<div class="grid min-h-0 grid-cols-2 gap-3 overflow-y-auto sm:grid-cols-3 lg:grid-cols-4">
			{#each images as image}
				<button
					type="button"
					class="pick"
					onclick={() => {
						set_image(image.id);
					}}
					title="{$t('words.select')}: {image.filename ?? 'image'}"
				>
					<img
						src="/api/v1/storage/download/{image.id}"
						loading="lazy"
						alt={image.alt_text ?? ''}
						class="aspect-[4/3] w-full rounded-[12px] object-cover"
					/>
					<span class="mt-2 block truncate text-xs text-ink-muted"
						>{image.filename ?? 'No name available'}</span
					>
				</button>
			{/each}
		</div>
	{/await}
</div>

<style>
	.panel {
		background: rgba(14, 10, 46, 0.94);
	}
	.close {
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
		border-radius: 999px;
		background: var(--fill-glass);
	}
	.pick {
		padding: 8px;
		border-radius: 16px;
		background: var(--fill-glass);
		text-align: left;
	}
	.pick:hover {
		background: var(--fill-glass-strong);
	}
	.pick:focus-visible,
	.close:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
</style>
