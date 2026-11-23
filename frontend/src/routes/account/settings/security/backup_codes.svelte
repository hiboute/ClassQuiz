<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	let { backup_code = $bindable() } = $props();

	let already_downloaded = false;

	const download_code = (force = false) => {
		if (already_downloaded && !force) {
			return;
		}
		const el = document.createElement('a');
		el.setAttribute('href', `data:text/plain;charset=utf-8,${backup_code}`);
		el.setAttribute('download', 'LiveQuiz-Backup-Code.txt');
		el.style.display = 'none';
		document.body.appendChild(el);
		el.click();
		document.body.removeChild(el);
		already_downloaded = true;
	};
</script>

<div class="w-screen h-screen fixed top-0 left-0 p-4 sm:p-16 lg:p-24 z-50 bg-[#05040f]/70 backdrop-blur-sm">
	<div class="w-full h-full">
		<button
			class="bg-[#1a1440] px-4 py-2 rounded-t-[18px] hover:bg-[#2a2160] transition"
			onclick={() => {
				backup_code = undefined;
			}}
			>{$t('words.close')}
		</button>
		<div
			class="bg-[#1a1440] rounded-b-[25px] rounded-tr-[25px] p-6 overflow-auto w-full h-full flex flex-col"
		>
			<h2 class="text-3xl m-auto">{$t('security_settings.backup_codes.your_backup_code')}</h2>
			<p
				class="select-all font-mono text-xl m-auto"
				onclick={() => {
					download_code(false);
				}}
			>
				{backup_code}
			</p>
			<p class="m-auto">{$t('security_settings.backup_codes.save_somewhere_save')}</p>
			<button
				onclick={() => {
					download_code(true);
				}}
				class="m-auto bt-btn-primary"
				>{$t('security_settings.backup_codes.download_code')}
			</button>
		</div>
	</div>
</div>
