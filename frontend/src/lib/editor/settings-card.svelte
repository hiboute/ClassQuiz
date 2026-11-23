<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { EditorData } from '$lib/quiz_types';
	import { reach, type Schema } from 'yup';
	import { dataSchema } from '$lib/yupSchemas';
	import Loading from '$lib/editor/Loading.svelte';
	import EdIcon from '$lib/editor/EdIcon.svelte';
	import { plainText } from '$lib/editor/editor_meta';

	let uppyOpen = $state(false);
	let bg_uppy_open = $state(false);

	interface Props {
		edit_id: string;
		data: EditorData;
	}

	let { edit_id = $bindable(), data = $bindable() }: Props = $props();

	let custom_bg_color = $state(Boolean(data.background_color));
	let other_open = $state(Boolean(data.background_color || data.background_image));

	$effect(() => {
		data.background_color = custom_bg_color ? (data.background_color ?? '#170d43') : undefined;
	});

	const titleSchema = reach(dataSchema, 'title') as Schema;
	const descriptionSchema = reach(dataSchema, 'description') as Schema;
	const title_ok = $derived(titleSchema.isValidSync(data.title));
	const desc_ok = $derived(descriptionSchema.isValidSync(data.description));
	const desc_len = $derived((data.description ?? '').length);
</script>

<div class="mx-auto grid max-w-[1180px] gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
	<div class="flex min-w-0 flex-col gap-5">
		<section class="bt-glass bt-glass-faint p-5 lg:p-6">
			<span class="bt-eyebrow mb-3 text-[11px] text-ink-muted">Quiz title</span>
			<div class="q-title relative">
				{#await import('$lib/inline-editor.svelte')}
					<Loading />
				{:then c}
					<c.default bind:text={data.title} />
				{/await}
				{#if !plainText(data.title)}
					<span class="q-placeholder" aria-hidden="true">Name your quiz</span>
				{/if}
			</div>
			{#if !title_ok}
				<p class="hint-warn mt-2"><EdIcon name="warn" size={14} /> 3 to 300 characters.</p>
			{/if}

			<label class="mt-6 block">
				<span class="bt-eyebrow mb-3 text-[11px] text-ink-muted">Description</span>
				<textarea
					placeholder="What is this quiz about? Shown to you and on the quiz page."
					bind:value={data.description}
					rows="3"
					maxlength="500"
					class="bt-input desc"
				></textarea>
			</label>
			<div class="mt-2 flex items-center gap-2 text-xs text-ink-muted">
				{#if !desc_ok}
					<span class="hint-warn"><EdIcon name="warn" size={14} /> 3 to 500 characters.</span>
				{/if}
				<span class="ml-auto tabular-nums">{desc_len} / 500</span>
			</div>
		</section>

		<section class="bt-glass bt-glass-faint p-5 lg:p-6">
			<span class="bt-eyebrow mb-3 text-[11px] text-ink-muted">Who can see it</span>
			<div class="seg" role="radiogroup" aria-label="Visibility">
				<button
					type="button"
					role="radio"
					aria-checked={!data.public}
					class="seg-item"
					class:seg-on={!data.public}
					onclick={() => (data.public = false)}
				>
					<EdIcon name="lock" size={18} />
					<span>
						<span class="block font-black uppercase tracking-[1px]">Private</span>
						<span class="block text-xs opacity-75">Only you can find and host it</span>
					</span>
				</button>
				<button
					type="button"
					role="radio"
					aria-checked={data.public}
					class="seg-item"
					class:seg-on={data.public}
					onclick={() => (data.public = true)}
				>
					<EdIcon name="globe" size={18} />
					<span>
						<span class="block font-black uppercase tracking-[1px]">Public</span>
						<span class="block text-xs opacity-75">Listed in Explore for everyone</span>
					</span>
				</button>
			</div>
		</section>

		<section class="bt-glass bt-glass-faint p-5 lg:p-6">
			<button
				type="button"
				class="flex w-full items-center gap-3 text-left"
				aria-expanded={other_open}
				onclick={() => (other_open = !other_open)}
			>
				<span class="flex-1">
					<span class="bt-eyebrow text-[11px] text-ink-muted">Other views</span>
					<span class="block text-sm text-ink-muted">
						Background colour and image. Live game screens always use the colour
						worlds of the event.
					</span>
				</span>
				<EdIcon name={other_open ? 'up' : 'down'} size={20} />
			</button>
			{#if other_open}
				<div class="mt-5 grid gap-5 md:grid-cols-2">
					<div>
						<span class="mb-2 block text-sm font-bold">Background colour</span>
						<div class="flex items-center gap-3">
							<label class="flex cursor-pointer items-center gap-3">
								<input type="checkbox" class="switch" bind:checked={custom_bg_color} />
								<span class="text-sm">{custom_bg_color ? 'Custom' : 'Default'}</span>
							</label>
							{#if custom_bg_color}
								<label class="swatch" style="background:{data.background_color}">
									<span class="sr-only">Pick a background colour</span>
									<input type="color" class="sr-only" bind:value={data.background_color} />
								</label>
							{/if}
						</div>
					</div>
					<div>
						<span class="mb-2 block text-sm font-bold">Background image</span>
						{#if data.background_image}
							<div class="flex items-center gap-3">
								<img
									src="/api/v1/storage/download/{data.background_image}"
									alt="Background"
									class="h-14 w-24 rounded-[10px] object-cover"
								/>
								<button
									type="button"
									class="bt-btn-ghost small-pill"
									onclick={() => {
										data.background_image = undefined;
									}}>Remove</button
								>
							</div>
						{:else}
							{#await import('$lib/editor/uploader.svelte')}
								<Loading />
							{:then c}
								<c.default
									bind:modalOpen={bg_uppy_open}
									bind:data
									selected_question={-1}
									video_upload={false}
									compact={true}
								/>
							{/await}
						{/if}
					</div>
				</div>
			{/if}
		</section>
	</div>

	<aside class="flex min-w-0 flex-col gap-5">
		<section class="bt-glass bt-glass-faint p-5">
			<div class="mb-3 flex items-center gap-2">
				<EdIcon name="image" size={16} class="text-ink-muted" />
				<span class="bt-eyebrow text-[11px] text-ink-muted">Cover image</span>
			</div>
			{#if data.cover_image != undefined && data.cover_image !== ''}
				<div class="media relative">
					<img
						src="/api/v1/storage/download/{data.cover_image}"
						alt="Quiz cover"
						class="max-h-56 w-full rounded-[14px] object-contain"
					/>
					<button
						class="media-remove"
						type="button"
						aria-label="Remove the cover image"
						title="Remove the cover image"
						onclick={() => {
							data.cover_image = null;
						}}><EdIcon name="trash" size={16} /></button
					>
				</div>
			{:else}
				{#await import('$lib/editor/uploader.svelte')}
					<Loading />
				{:then c}
					<c.default bind:modalOpen={uppyOpen} bind:data video_upload={false} />
				{/await}
			{/if}
			<p class="mt-3 text-xs text-ink-muted">
				Shown on your dashboard and on the quiz page, not during the game.
			</p>
		</section>

		<section class="bt-glass bt-glass-faint p-5">
			<span class="bt-eyebrow mb-3 text-[11px] text-ink-muted">At a glance</span>
			<dl class="grid grid-cols-2 gap-3">
				<div class="stat">
					<dt class="text-xs text-ink-muted">Questions</dt>
					<dd class="bt-num text-[32px]">
						{data.questions.filter((q) => q.type !== 'SLIDE').length}
					</dd>
				</div>
				<div class="stat">
					<dt class="text-xs text-ink-muted">Minutes, about</dt>
					<dd class="bt-num text-[32px]">
						{Math.max(
							1,
							Math.round(
								data.questions.reduce(
									(s, q) => s + (q.type === 'SLIDE' ? 15 : (parseInt(String(q.time), 10) || 0) + 15),
									0
								) / 60
							)
						)}
					</dd>
				</div>
			</dl>
		</section>
	</aside>
</div>

<style>
	.q-title > :global(div) {
		width: 100%;
		border: 0;
		border-radius: 18px;
	}
	.q-title :global(.ck.ck-editor__editable_inline),
	.q-title :global([contenteditable]) {
		width: 100%;
		min-height: 72px;
		padding: 16px 20px;
		border: 0 !important;
		border-radius: 18px;
		background: var(--fill-glass) !important;
		color: var(--ink) !important;
		font-family: var(--bt-font);
		font-size: 28px;
		font-weight: 900;
		line-height: 1.15;
		text-align: left;
		text-transform: uppercase;
		box-shadow: none !important;
	}
	.q-title :global(.ck.ck-editor__editable_inline.ck-focused),
	.q-title :global([contenteditable]:focus) {
		box-shadow: 0 0 0 3px var(--accent-sky) !important;
		outline: none;
	}
	.q-title :global(.ck.ck-editor__editable_inline > p) {
		margin: 0;
	}
	.q-placeholder {
		position: absolute;
		left: 21px;
		top: 50%;
		transform: translateY(-50%);
		font-size: 28px;
		font-weight: 900;
		text-transform: uppercase;
		color: var(--ink-muted);
		opacity: 0.55;
		pointer-events: none;
	}
	.desc {
		resize: vertical;
		min-height: 96px;
		font-size: 16px;
		border-radius: 18px;
	}
	.hint-warn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		color: #ffd3fb;
	}
	.seg {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 4px;
		padding: 4px;
		border-radius: 20px;
		background: var(--fill-deep);
	}
	.seg-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px 14px;
		border-radius: 16px;
		text-align: left;
		color: var(--ink-muted);
		font-size: 14px;
	}
	.seg-item:hover {
		background: var(--fill-glass);
		color: var(--ink);
	}
	.seg-on,
	.seg-on:hover {
		background: var(--fill-glass-strong);
		color: var(--ink);
	}
	.seg-item:focus-visible,
	.media-remove:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	.media {
		border-radius: 14px;
		background: var(--fill-deep);
		padding: 6px;
	}
	.media-remove {
		position: absolute;
		top: 10px;
		right: 10px;
		display: grid;
		place-items: center;
		width: 34px;
		height: 34px;
		border-radius: 999px;
		background: var(--fill-deep);
	}
	.stat {
		padding: 12px;
		border-radius: 16px;
		background: var(--fill-glass);
	}
	.stat dd {
		margin-top: 8px;
	}
	.swatch {
		display: block;
		width: 40px;
		height: 32px;
		border-radius: 10px;
		cursor: pointer;
		box-shadow: 0 0 0 2px var(--fill-glass-strong);
	}
	.small-pill {
		min-height: 36px;
		padding: 0 16px;
		font-size: 12px;
		letter-spacing: 2px;
	}
	.switch {
		appearance: none;
		flex: none;
		position: relative;
		width: 48px;
		height: 28px;
		border-radius: 999px;
		background: var(--fill-glass-strong);
		cursor: pointer;
		transition: background-color 150ms ease;
	}
	.switch::after {
		content: '';
		position: absolute;
		top: 3px;
		left: 3px;
		width: 22px;
		height: 22px;
		border-radius: 999px;
		background: var(--ink);
		transition: transform 150ms ease;
	}
	.switch:checked {
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
	}
	.switch:checked::after {
		transform: translateX(20px);
		background: var(--ink-dark);
	}
</style>
