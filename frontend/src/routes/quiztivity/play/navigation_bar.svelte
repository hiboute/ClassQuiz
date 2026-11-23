<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import BrownButton from '$lib/components/buttons/brown.svelte';
	import { getLocalization } from '$lib/i18n';

	interface Props {
		current_slide_index: number;
		question_count: number;
	}

	let { current_slide_index = $bindable(), question_count }: Props = $props();

	const { t } = getLocalization();
</script>

<div
	class="bt-glass bt-glass-deep mt-auto mx-2 mb-2 min-h-[7vh] flex justify-between !rounded-card"
>
	<div class="my-auto justify-start ml-4">
		<BrownButton
			disabled={current_slide_index < 1}
			onclick={() => {
				current_slide_index -= 1;
			}}>{$t('words.back')}</BrownButton
		>
	</div>
	<div class="my-auto bt-num font-black">
		{current_slide_index + 1}/{question_count}
	</div>
	<div class="my-auto justify-end mr-4">
		<BrownButton
			disabled={current_slide_index >= question_count - 1}
			onclick={() => {
				current_slide_index += 1;
			}}>{$t('words.next')}</BrownButton
		>
	</div>
</div>
