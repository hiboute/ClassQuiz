<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->
<script lang="ts">
	import { portal } from '$lib/editor/portal';
	import { Dashboard as SvelteDashboard } from '@uppy/svelte';
	import Uppy from '@uppy/core';
	import DropTarget from '@uppy/drop-target';
	import XHRUpload from '@uppy/xhr-upload';
	import ImageEditor from '@uppy/image-editor';
	import Dashboard from '@uppy/dashboard';
	import Compressor from '@uppy/compressor';
	import { fade, scale } from 'svelte/transition';

	// CSS imports
	import '@uppy/core/dist/style.css';
	import '@uppy/dashboard/dist/style.css';
	import '@uppy/drop-target/dist/style.css';
	import '@uppy/image-editor/dist/style.css';
	import type { EditorData } from '../quiz_types';
	import { getLocalization } from '$lib/i18n';
	import { onMount } from 'svelte';
	import Library from '$lib/editor/uploader/Library.svelte';
	import Pixabay from '$lib/editor/uploader/Pixabay.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';

	const { t } = getLocalization();
	let {
		modalOpen = $bindable(),
		data = $bindable(),
		selected_question,
		video_upload = false,
		library_enabled = true,
		compact = false
	}: {
		modalOpen: boolean;
		data: EditorData;
		selected_question?: number;
		video_upload: boolean;
		library_enabled?: boolean;
		/** a small pill instead of the drop zone */
		compact?: boolean;
	} = $props();

	// eslint-disable-next-line no-undef
	let video_popup: undefined | WindowProxy = $state(undefined);

	let selected_type: AvailableUploadTypes | null = $state(null);

	// eslint-disable-next-line no-unused-vars
	enum AvailableUploadTypes {
		// eslint-disable-next-line no-unused-vars
		Image,
		// eslint-disable-next-line no-unused-vars
		Video,
		// eslint-disable-next-line no-unused-vars
		Library,
		// eslint-disable-next-line no-unused-vars
		Pixabay
	}

	const uppy = new Uppy()
		.use(DropTarget, {
			target: document.body
		})
		.use(Dashboard)
		.use(ImageEditor, {
			target: Dashboard,
			quality: 0.8
		})
		.use(Compressor, {
			quality: 0.6
		})
		.use(XHRUpload, {
			endpoint: `/api/v1/storage/`
		});
	const properties = {
		inline: true,
		theme: 'dark',
		restrictions: {
			maxFileSize: 10_490_000,
			maxNumberOfFiles: 1,
			allowedFileTypes: ['image/*']
		}
	};
	let image_id: string;
	uppy.on('upload-success', (file, response) => {
		image_id = response.body.id;
	});
	uppy.on('complete', () => {
		if (selected_question === undefined) {
			data.cover_image = image_id;
		} else if (selected_question === -1) {
			data.background_image = image_id;
		} else {
			data.questions[selected_question].image = image_id;
		}

		modalOpen = false;
		selected_type = null;
	});

	const close = () => {
		modalOpen = false;
		selected_type = null;
	};

	onMount(() => {
		const on_storage = (e: StorageEvent) => {
			if (e.key !== 'video_upload_id' || !e.newValue) {
				return;
			}
			localStorage.removeItem('video_upload_id');
			data.questions[selected_question].image = e.newValue;
			selected_type = null;
			modalOpen = false;
		};
		const on_key = (e: KeyboardEvent) => {
			if (e.key === 'Escape') close();
		};
		window.addEventListener('storage', on_storage);
		window.addEventListener('keydown', on_key);
		return () => {
			window.removeEventListener('storage', on_storage);
			window.removeEventListener('keydown', on_key);
		};
	});

	const upload_video = async () => {
		video_popup = window.open(
			'/edit/videos',
			'_blank',
			'popup=true,toolbar=false,menubar=false,location=false,'
		);
		video_popup?.addEventListener('beforeunload', () => {
			video_popup = undefined;
		});
	};

	const handle_on_click = (e: Event) => {
		if (e.target === e.currentTarget) close();
	};

	const sources = $derived(
		[
			{
				type: AvailableUploadTypes.Image,
				icon: 'image' as const,
				label: $t('words.image'),
				hint: 'Upload from this computer',
				enabled: true
			},
			{
				type: AvailableUploadTypes.Video,
				icon: 'video' as const,
				label: $t('words.video'),
				hint: video_upload ? 'MP4, compressed before upload' : 'Not available here',
				enabled: video_upload
			},
			{
				type: AvailableUploadTypes.Library,
				icon: 'folder' as const,
				label: $t('words.library'),
				hint: 'Reuse one of your images',
				enabled: library_enabled,
				hidden: !library_enabled
			},
			{
				type: AvailableUploadTypes.Pixabay,
				icon: 'search' as const,
				label: 'Pixabay',
				hint: 'Search free stock photos',
				enabled: true
			}
		].filter((s) => !s.hidden)
	);
</script>

{#if modalOpen}
	<div
	use:portal
		class="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(5,3,20,0.72)] p-4"
		onclick={handle_on_click}
		role="presentation"
		transition:fade={{ duration: 100 }}
	>
		{#if selected_type === null}
			<div
				class="bt-glass panel w-full max-w-xl p-6"
				role="dialog"
				aria-modal="true"
				aria-labelledby="uploader-title"
				transition:scale={{ duration: 120, start: 0.97 }}
			>
				<div class="mb-5 flex items-start gap-4">
					<div class="flex-1">
						<span class="bt-eyebrow text-[11px] text-ink-muted">Media</span>
						<h2 id="uploader-title" class="bt-headline text-2xl">
							{$t('uploader.select_upload_type')}
						</h2>
					</div>
					<button type="button" class="close" aria-label="Close" onclick={close}
						><EdIcon name="x" size={20} /></button
					>
				</div>
				<div class="grid grid-cols-2 gap-3">
					{#each sources as s}
						<button
							type="button"
							class="source"
							disabled={!s.enabled}
							onclick={() => (selected_type = s.type)}
						>
							<span class="source-icon"><EdIcon name={s.icon} size={22} /></span>
							<span class="block font-black uppercase tracking-[1px]">{s.label}</span>
							<span class="block text-xs text-ink-muted">{s.hint}</span>
						</button>
					{/each}
				</div>
			</div>
		{:else if selected_type === AvailableUploadTypes.Image}
			<div class="uppy-wrap w-full max-w-2xl" transition:fade={{ duration: 100 }}>
				<SvelteDashboard {uppy} width="100%" {properties} />
			</div>
		{:else if selected_type === AvailableUploadTypes.Video}
			<div
				class="bt-glass panel w-full max-w-xl p-6"
				role="dialog"
				aria-modal="true"
				transition:fade={{ duration: 100 }}
			>
				<span class="bt-eyebrow text-[11px] text-ink-muted">Media</span>
				<h2 class="bt-headline mb-4 text-2xl">{$t('uploader.upload_a_video')}</h2>
				{#if video_popup}
					<p class="text-ink-muted">
						{$t('uploader.upload_video_popup_notice')}
					</p>
				{:else}
					<button type="button" class="bt-btn-primary bt-btn-block" onclick={upload_video}
						>{$t('uploader.upload_video')}</button
					>
				{/if}
			</div>
		{:else if selected_type === AvailableUploadTypes.Library}
			<Library bind:data {selected_question} bind:modalOpen />
		{:else if selected_type === AvailableUploadTypes.Pixabay}
			<Pixabay bind:data {selected_question} bind:modalOpen />
		{/if}
	</div>
{/if}

<button
	class="add-media"
	class:add-media-compact={compact}
	type="button"
	onclick={() => {
		modalOpen = true;
	}}
>
	<EdIcon name="image" size={compact ? 18 : 26} />
	<span>{$t('uploader.add_image')}</span>
	{#if !compact}
		<span class="text-xs font-normal tracking-normal normal-case text-ink-muted"
			>Image, video, your library or Pixabay</span
		>
	{/if}
</button>

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
	.close:hover {
		background: var(--fill-glass-strong);
	}
	.source {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 4px;
		padding: 16px;
		border-radius: 18px;
		background: var(--fill-glass);
		text-align: left;
		transition: background-color 120ms ease;
	}
	.source:hover:not(:disabled) {
		background: var(--fill-glass-strong);
	}
	.source:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
	.source-icon {
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
		margin-bottom: 6px;
		border-radius: 12px;
		background: var(--fill-deep);
	}
	.add-media {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 6px;
		width: 100%;
		min-height: 128px;
		padding: 16px;
		border-radius: 18px;
		background: var(--fill-deep);
		color: var(--ink);
		font-weight: 700;
		font-size: 13px;
		letter-spacing: 2px;
		text-transform: uppercase;
		transition: background-color 120ms ease;
	}
	.add-media:hover {
		background: var(--fill-glass-mid);
	}
	.add-media-compact {
		flex-direction: row;
		min-height: 40px;
		width: auto;
		padding: 0 16px;
		border-radius: 999px;
		background: var(--fill-glass);
	}
	.add-media:focus-visible,
	.source:focus-visible,
	.close:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.uppy-wrap :global(.uppy-Dashboard-inner) {
		border: 0;
		border-radius: 25px;
		overflow: hidden;
		background-color: #0e0a2e;
	}
</style>
