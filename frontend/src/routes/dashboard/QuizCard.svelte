<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- One quiz on the organiser dashboard: title, counts, Start / Edit / Results, and a menu. -->
<script lang="ts">
	interface Props {
		item: {
			id: string;
			type: 'quiz' | 'quiztivity';
			title: string;
			description?: string;
			public?: boolean;
			questions?: unknown[];
			pages?: unknown[];
			plays?: number;
		};
		onstart: () => void;
		onanalytics: () => void;
		ondownload: () => void;
		ondelete: () => void;
	}

	let { item, onstart, onanalytics, ondownload, ondelete }: Props = $props();

	let menu_open = $state(false);
	let menu_el: HTMLElement | undefined = $state();

	const is_quiz = $derived(item.type === 'quiz');
	const count = $derived(is_quiz ? (item.questions?.length ?? 0) : (item.pages?.length ?? 0));
	const count_label = $derived(
		is_quiz ? (count === 1 ? 'question' : 'questions') : count === 1 ? 'page' : 'pages'
	);
	const description = $derived((item.description ?? '').replace(/<[^>]*>/g, '').trim());
	const edit_href = $derived(
		is_quiz ? `/edit?quiz_id=${item.id}` : `/quiztivity/edit?id=${item.id}`
	);

	const on_window_click = (e: MouseEvent) => {
		if (menu_open && menu_el && !menu_el.contains(e.target as Node)) menu_open = false;
	};
	const on_window_key = (e: KeyboardEvent) => {
		if (menu_open && e.key === 'Escape') menu_open = false;
	};
</script>

<svelte:window onclick={on_window_click} onkeydown={on_window_key} />

<article
	class="bt-glass bt-glass-faint h-full p-5 sm:p-6 flex flex-col gap-4"
	class:card-menu-open={menu_open}
>
	<div class="flex items-start gap-3">
		<div class="min-w-0 flex-1">
			<div class="flex flex-wrap items-center gap-2">
				<span class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
					>{is_quiz ? 'Quiz' : 'Quiztivity'}</span
				>
				{#if is_quiz && item.public === false}
					<span class="rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] uppercase tracking-[2px]"
						>Private</span
					>
				{/if}
			</div>
			<h2 class="mt-2 text-xl sm:text-2xl font-black leading-tight break-words line-clamp-2">
				{@html item.title}
			</h2>
		</div>
		<div class="relative z-30 shrink-0" bind:this={menu_el}>
			<button
				type="button"
				class="h-10 w-10 -me-2 -mt-1 rounded-full hover:bg-white/10 flex items-center justify-center"
				aria-label="More actions for this quiz"
				aria-haspopup="menu"
				aria-expanded={menu_open}
				onclick={() => (menu_open = !menu_open)}
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"
					><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle
						cx="19"
						cy="12"
						r="2"
					/></svg
				>
			</button>
			{#if menu_open}
				<div
					role="menu"
					class="absolute end-0 top-11 z-20 w-52 overflow-hidden rounded-[18px] bg-[#1a1440] shadow-2xl py-2"
				>
					{#if is_quiz}
						<a
							role="menuitem"
							href="/view/{item.id}"
							class="block px-4 py-2.5 hover:bg-white/10"
							class:pointer-events-none={!item.public}
							class:opacity-40={!item.public}>Public page</a
						>
						<button
							role="menuitem"
							type="button"
							class="block w-full text-start px-4 py-2.5 hover:bg-white/10"
							onclick={() => {
								menu_open = false;
								onanalytics();
							}}>Views and plays</button
						>
						<button
							role="menuitem"
							type="button"
							class="block w-full text-start px-4 py-2.5 hover:bg-white/10"
							onclick={() => {
								menu_open = false;
								ondownload();
							}}>Download</button
						>
					{/if}
					<button
						role="menuitem"
						type="button"
						class="block w-full text-start px-4 py-2.5 hover:bg-white/10 text-[#ff9db0]"
						onclick={() => {
							menu_open = false;
							ondelete();
						}}>Delete</button
					>
				</div>
			{/if}
		</div>
	</div>

	{#if description}
		<p class="text-sm text-ink-muted line-clamp-2 -mt-1">{description}</p>
	{/if}

	<div class="flex items-baseline gap-5 mt-auto pt-1">
		<p>
			<span class="bt-num text-[34px]">{count}</span>
			<span class="ms-1 text-sm text-ink-muted">{count_label}</span>
		</p>
		{#if is_quiz && item.plays !== undefined}
			<p>
				<span class="bt-num text-[34px]">{item.plays}</span>
				<span class="ms-1 text-sm text-ink-muted">{item.plays === 1 ? 'game' : 'games'}</span>
			</p>
		{/if}
	</div>

	<div class="grid gap-2 {is_quiz ? 'grid-cols-[1.25fr_1fr_1fr]' : 'grid-cols-2'}">
		{#if is_quiz}
			<button
				type="button"
				class="bt-btn-primary card-btn"
				onclick={onstart}
				disabled={count === 0}
				title={count === 0 ? 'Add a question first' : undefined}
			>
				<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"
					><path d="M7 4.5v15l13-7.5z" /></svg
				>
				Start
			</button>
		{:else}
			<a href="/quiztivity/play?id={item.id}" class="bt-btn-primary card-btn">Play</a>
		{/if}
		<a href={edit_href} class="bt-btn-ghost card-btn">Edit</a>
		{#if is_quiz}
			<a href="/results?quiz={item.id}" class="bt-btn-ghost card-btn">Results</a>
		{/if}
	</div>
</article>

<style>
	/* The card is a stacking context (backdrop-filter): lift it above the
	   next cards while its menu is open, so the menu is never covered. */
	.card-menu-open {
		position: relative;
		z-index: 30;
	}
	.card-btn {
		min-width: 0;
		padding: 0 10px;
		font-size: 14px;
		letter-spacing: 2px;
	}
</style>
