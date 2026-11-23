<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import World from '$lib/brand/World.svelte';

	navbarVisible.visible = true;

	const { t } = getLocalization();
	let file_input: FileList | undefined = $state();
	let is_loading = $state(false);
	let error = $state('');

	const file_submit = async (e: Event) => {
		e.preventDefault();
		error = '';
		const file = file_input?.[0];
		if (!file) {
			return;
		}
		is_loading = true;
		const formdata = new FormData();
		formdata.append('file', file);
		let res: Response;
		if (file.name.endsWith('.xlsx')) {
			res = await fetch('/api/v1/quiz/excel-import', {
				method: 'POST',
				body: formdata
			});
		} else if (file.name.endsWith('.cqa')) {
			res = await fetch('/api/v1/eximport/', {
				method: 'POST',
				body: formdata
			});
		} else {
			error = 'Choose a .cqa or .xlsx file.';
			is_loading = false;
			return;
		}

		if (res.status === 200) {
			window.location.href = '/dashboard';
			return;
		}
		let detail = '';
		try {
			const body = await res.json();
			detail = typeof body?.detail === 'string' ? body.detail : '';
		} catch {
			detail = '';
		}
		error = detail ? `The import did not work: ${detail}.` : 'The import did not work.';
		is_loading = false;
	};
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz - Import</title>
</svelte:head>

<World world="midnight" fullscreen={false} class="min-h-[calc(100dvh-4rem)]">
	<div class="max-w-xl mx-auto px-4 py-12">
		<span class="bt-eyebrow text-ink-muted text-center">Live Quiz</span>
		<h1 class="mt-3 text-center text-4xl font-black uppercase tracking-wide">
			{$t('words.import')}
		</h1>

		<form onsubmit={file_submit} class="bt-glass mt-8 p-6 sm:p-8 flex flex-col gap-5">
			<h2 class="bt-eyebrow">{$t('import_page.classquiz_quiz')}</h2>
			<p class="text-ink-muted">{$t('import_page.this_side_classquiz')}</p>
			<label class="flex flex-col gap-2">
				<span class="text-sm text-ink-muted">{$t('import_page.upload_file_ending')}</span>
				<input
					id="file"
					bind:files={file_input}
					name="file"
					type="file"
					accept=".cqa,.xlsx"
					class="bt-input file:mr-4 file:rounded-full file:border-0 file:bg-white/15 file:px-4 file:py-1.5 file:text-ink"
				/>
			</label>
			<p class="text-ink-muted text-sm">{$t('import_page.this_side_classquiz_excel')}</p>
			<details class="text-sm text-ink-muted">
				<summary class="cursor-pointer text-ink"
					>{$t('import_page.download_template_here')}</summary
				>
				<ul class="mt-3 list-disc pl-5 space-y-1">
					<li>Cell C5: quiz title. Cell C6: description (3 to 500 characters).</li>
					<li>From row 14, one question per row.</li>
					<li>Column B: question. Columns C to F: answers 1 to 4.</li>
					<li>Column G: time in seconds, up to 120.</li>
					<li>Column H: the numbers of the correct answers, for example 13.</li>
				</ul>
			</details>
			{#if error}
				<p class="text-sm text-ink" role="alert">{error}</p>
			{/if}
			<button
				class="bt-btn-primary bt-btn-lg bt-btn-block"
				disabled={!file_input?.length || is_loading}
				type="submit"
			>
				{is_loading ? 'Importing' : $t('words.submit')}
			</button>
		</form>
	</div>
</World>
