<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import type { PageData } from './$types';
	import BrownButton from '$lib/components/buttons/brown.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz - Moderation</title>
</svelte:head>

<div class="max-w-5xl mx-auto px-4 py-8">
	<span class="bt-eyebrow text-ink-muted">Live Quiz</span>
	<h1 class="mt-2 mb-6 text-3xl font-black uppercase tracking-wide">Moderation</h1>
	<div class="flex flex-col gap-4">
		{#each data.quizzes as quiz}
			<div class="bt-glass w-full min-h-[20vh] p-4 flex flex-col gap-3">
				<div class="grid grid-cols-3 h-full gap-4">
					<div class="hidden lg:flex w-auto h-full items-center relative">
						{#if quiz.cover_image}
							<img
								src="/api/v1/storage/download/{quiz.cover_image}"
								alt="user provided"
								loading="lazy"
								class="shrink-0 max-w-full max-h-full absolute rounded-tile"
							/>
						{/if}
					</div>
					<div class="my-auto mx-auto max-h-full overflow-hidden">
						<p class="text-xl text-center font-bold">{@html quiz.title}</p>
						<p class="text-sm text-center text-ink-muted text-clip overflow-hidden">
							{@html quiz.description ?? ''}
						</p>
					</div>
					<div class="flex justify-center">
						<p class="m-auto text-ink-muted">
							Questions <span class="bt-num text-ink font-black"
								>{quiz.questions.length}</span
							>
						</p>
					</div>
				</div>
				<div class="flex w-full">
					<BrownButton href="/view/{quiz.id}?mod=true&autoExpand=true&autoReturn=true"
						>View</BrownButton
					>
				</div>
			</div>
		{/each}
	</div>
	<div class="flex mt-6">
		<div class="grid grid-cols-3 gap-4 mx-auto items-center">
			<BrownButton
				disabled={data.page === '1'}
				href="/moderation?page={parseInt(data.page) - 1}">Previous page</BrownButton
			>
			<p class="m-auto text-ink-muted">Page {data.page}</p>
			<BrownButton
				disabled={data.quizzes.length !== 20}
				href="/moderation?page={parseInt(data.page) + 1}">Next page</BrownButton
			>
		</div>
	</div>
</div>
