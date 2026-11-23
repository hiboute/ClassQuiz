<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->
<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import Modal from '$lib/components/organiser/Modal.svelte';

	const { t } = getLocalization();
	interface Props {
		quiz_id?: string | null;
	}

	let { quiz_id = $bindable(null) }: Props = $props();
</script>

{#if quiz_id}
	<Modal label={$t('downloader.select_download_type')} world="midnight" onclose={() => (quiz_id = null)}>
		<div class="px-6 py-8 sm:p-10">
			<span class="bt-eyebrow text-ink-muted mb-3">Download</span>
			<h2 class="bt-headline text-[26px] sm:text-[34px] pe-10">
				{$t('downloader.select_download_type')}
			</h2>
			<div class="mt-8 grid gap-3 sm:grid-cols-2">
				<a href="/api/v1/eximport/{quiz_id}" class="bt-btn-ghost bt-btn-block"
					>{$t('downloader.own_format')}</a
				>
				<a href="/api/v1/eximport/excel/{quiz_id}" class="bt-btn-ghost bt-btn-block"
					>{$t('downloader.excel_format')}</a
				>
			</div>
			<p class="mt-5 text-sm text-ink-muted">{$t('downloader.help')}</p>
		</div>
	</Modal>
{/if}
