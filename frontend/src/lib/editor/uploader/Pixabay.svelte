<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
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

	let page = $state(1);
	let search_term = $state('');
	let loading = $state(false);

	const { t } = getLocalization();

	const set_image = async (id: string) => {
		loading = true;
		const res = await fetch(`/api/v1/pixabay/save?id=${id}`, {
			method: 'POST'
		});
		const json = await res.json();
		const storage_id = json.id;
		if (selected_question === undefined) {
			data.cover_image = storage_id;
		} else if (selected_question === -1) {
			data.background_image = storage_id;
		} else {
			data.questions[selected_question].image = storage_id;
		}
		modalOpen = false;
	};

	const fetch_data = async () => {
		const res = await fetch(
			`/api/v1/pixabay/images?page=${page}&query=${encodeURIComponent(search_term)}`
		);
		return await res.json();
	};

	let fetched_data = $state(fetch_data());
</script>

<div
	class="bt-glass panel flex max-h-[85dvh] w-full max-w-4xl flex-col p-6"
	role="dialog"
	aria-modal="true"
	aria-labelledby="pixabay-title"
>
	<div class="mb-4 flex items-start gap-4">
		<div class="flex-1">
			<span class="bt-eyebrow text-[11px] text-ink-muted">Media</span>
			<h2 id="pixabay-title" class="bt-headline text-2xl">{$t('uploader.images_by_pixabay')}</h2>
			<a href="https://pixabay.com" target="_blank" rel="noopener" class="text-xs text-ink-muted underline"
				>{$t('uploader.visit_pixabay')}</a
			>
		</div>
		<button type="button" class="close" aria-label="Close" onclick={() => (modalOpen = false)}
			><EdIcon name="x" size={20} /></button
		>
	</div>

	<form
		class="flex gap-2"
		onsubmit={(e) => {
			e.preventDefault();
			e.stopPropagation();
			page = 1;
			fetched_data = fetch_data();
		}}
	>
		<input
			class="bt-input search"
			bind:value={search_term}
			placeholder="Search, in English"
			aria-label={$t('words.search')}
		/>
		<button type="submit" class="bt-btn-primary">
			<EdIcon name="search" size={18} />{$t('words.search')}
		</button>
	</form>
	<span class="mt-2 text-xs text-ink-muted">{$t('uploader.search_english_only')}</span>

	{#if loading}
		<Loading label="Saving the image" />
	{:else}
		{#await fetched_data}
			<Loading />
		{:then result}
			<div class="mt-4 grid min-h-0 grid-cols-2 gap-3 overflow-y-auto sm:grid-cols-3">
				{#each result?.hits ?? [] as image}
					<button
						type="button"
						class="pick"
						onclick={() => {
							set_image(image.id);
						}}
						title={$t('words.select')}
					>
						<img
							src={image.webformatURL}
							loading="lazy"
							alt={image.tags ?? ''}
							class="aspect-[4/3] w-full rounded-[12px] object-cover"
						/>
					</button>
				{/each}
			</div>
			<div class="mt-4 flex justify-between gap-2">
				<button
					type="button"
					class="bt-btn-ghost pager"
					disabled={page < 2}
					onclick={() => {
						page -= 1;
						fetched_data = fetch_data();
					}}
					>{$t('uploader.previous_page')}
				</button>
				<span class="self-center text-sm text-ink-muted tabular-nums">Page {page}</span>
				<button
					type="button"
					class="bt-btn-ghost pager"
					onclick={() => {
						page += 1;
						fetched_data = fetch_data();
					}}>{$t('uploader.next_page')}</button
				>
			</div>
		{/await}
	{/if}
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
	.search {
		flex: 1;
		padding: 10px 18px;
		font-size: 16px;
	}
	.pager {
		min-height: 40px;
		padding: 0 18px;
		font-size: 12px;
		letter-spacing: 2px;
	}
	.pick {
		padding: 6px;
		border-radius: 16px;
		background: var(--fill-glass);
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
