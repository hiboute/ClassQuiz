<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import { fade } from 'svelte/transition';
	// import MediaComponent from '$lib/editor/MediaComponent.svelte';
	import { onMount } from 'svelte';
	import Uploader from './uploader.svelte';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let edit_popup = $state(null);
	const images = data.images;

	const close_popup_handler = (e: Event) => {
		if (e.target !== e.currentTarget) return;
		edit_popup = null;
	};
	onMount(() => {
		window.onkeydown = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				edit_popup = null;
			}
		};
	});

	const save_image_metadata = async (e: Event) => {
		e.preventDefault();
		await fetch(`/api/v1/storage/meta/${edit_popup.id}`, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ filename: edit_popup.filename, alt_text: edit_popup.alt_text })
		});
		edit_popup = null;
		window.location.reload();
	};

	const delete_image = async (id: string) => {
		await fetch(`/api/v1/storage/meta/${id}`, { method: 'DELETE' });
		window.location.reload();
	};
</script>

<div class="mx-auto max-w-6xl px-4 pt-6 pb-16">
	<span class="bt-eyebrow text-[11px] text-ink-muted">Your media</span>
	<h1 class="bt-headline mt-1 text-3xl">Images and videos</h1>
	<p class="mt-2 text-ink-muted">
		{$t('file_dashboard.storage_usage', {
			used: (data.storage_usage.used / (1024 * 1024)).toFixed(2),
			total: (data.storage_usage.limit / (1024 * 1024)).toFixed(0),
			percent: ((data.storage_usage.used / data.storage_usage.limit) * 100).toFixed(0)
		})}
	</p>
	<div class="usage mt-3" aria-hidden="true">
		<span
			style="width:{Math.min(100, (data.storage_usage.used / data.storage_usage.limit) * 100)}%"
		></span>
	</div>
	<div class="mt-6 max-w-md">
		<Uploader />
	</div>
	<div class="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
		{#each images as image}
			<div
				class="bt-glass bt-glass-faint grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] gap-4 p-4 transition-opacity hover:opacity-100"
				class:opacity-50={image.quiztivities.length === 0 && image.quizzes.length === 0}
			>
				<img
					src="/api/v1/storage/download/{image.id}"
					class="m-auto max-h-[30vh] w-full rounded-[14px] object-contain"
					loading="lazy"
					alt={image.alt_text || $t('file_dashboard.not_available')}
				/>
				<div class="my-auto flex flex-col gap-1 text-sm">
					<p class="truncate font-bold">
						{$t('file_dashboard.filename', {
							filename: image.filename ?? $t('file_dashboard.missing')
						})}
					</p>
					<p class="text-ink-muted">
						{$t('file_dashboard.size', {
							size: (image.size / (1024 * 1024)).toFixed(2)
						})}
					</p>
					<p class="text-ink-muted">
						{$t('file_dashboard.caption', {
							caption: image.alt_text ?? $t('file_dashboard.missing')
						})}
					</p>
					<p class="text-ink-muted">
						{$t('file_dashboard.uploaded', {
							date: new Date(image.uploaded_at).toLocaleString()
						})}
					</p>
					<p class="text-ink-muted">
						{$t('file_dashboard.imported', {
							yes_or_no: image.imported ? $t('words.yes') : $t('words.no')
						})}
					</p>
					<div class="mt-3 flex flex-wrap gap-2">
						<button
							type="button"
							class="bt-btn-ghost small-pill"
							onclick={() => {
								edit_popup = image;
							}}
							>{$t('file_dashboard.edit_details')}
						</button>
						{#if image.quiztivities.length === 0 && image.quizzes.length === 0}
							<button
								type="button"
								class="bt-btn-ghost small-pill"
								onclick={() => {
									delete_image(image.id);
								}}>{$t('file_dashboard.delete_image')}</button
							>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
</div>

{#if edit_popup}
	<div
		transition:fade={{ duration: 100 }}
		class="fixed inset-0 z-40 flex items-center justify-center bg-[rgba(5,3,20,0.72)] p-4"
		onclick={close_popup_handler}
		role="presentation"
	>
		<div class="bt-glass panel w-full max-w-md p-6" role="dialog" aria-modal="true">
			<span class="bt-eyebrow text-[11px] text-ink-muted">Media</span>
			<h2 class="bt-headline mb-4 text-2xl">{$t('file_dashboard.edit_the_image')}</h2>
			<form class="flex flex-col gap-4" onsubmit={save_image_metadata}>
				<label class="flex flex-col gap-2">
					<span class="bt-eyebrow text-[10px] text-ink-muted"
						>{$t('file_dashboard.filename_word')}</span
					>
					<input class="bt-input field" id="name" type="text" bind:value={edit_popup.filename} />
				</label>
				<label class="flex flex-col gap-2">
					<span class="bt-eyebrow text-[10px] text-ink-muted"
						>{$t('file_dashboard.alt_text')}</span
					>
					<input
						class="bt-input field"
						class:field-missing={!edit_popup.alt_text}
						id="alt_text"
						type="text"
						bind:value={edit_popup.alt_text}
					/>
				</label>
				<button type="submit" class="bt-btn-primary bt-btn-block">{$t('words.save')}</button>
			</form>
		</div>
	</div>
{/if}

<style>
	.usage {
		height: 8px;
		max-width: 420px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		overflow: hidden;
	}
	.usage span {
		display: block;
		height: 100%;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
	}
	.small-pill {
		min-height: 36px;
		padding: 0 16px;
		font-size: 12px;
		letter-spacing: 1.5px;
	}
	.panel {
		background: rgba(14, 10, 46, 0.94);
	}
	.field {
		padding: 10px 16px;
		font-size: 16px;
		border-radius: 14px;
	}
	.field-missing {
		box-shadow: inset 0 0 0 2px rgba(249, 130, 250, 0.6);
	}
</style>
