<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import Modal from '$lib/components/organiser/Modal.svelte';

	const { t } = getLocalization();

	interface Props {
		quiz?: { title?: string; views?: number; plays?: number; likes?: number; dislikes?: number };
	}

	let { quiz = $bindable(undefined) }: Props = $props();

	const stats = $derived(
		quiz
			? [
					{ label: $t('words.view', { count: 2 }), value: quiz.views ?? 0 },
					{ label: 'Games', value: quiz.plays ?? 0 },
					{ label: $t('words.like', { count: 2 }), value: quiz.likes ?? 0 },
					{ label: $t('words.dislike', { count: 2 }), value: quiz.dislikes ?? 0 }
				]
			: []
	);
</script>

{#if quiz}
	<Modal label={$t('words.analytics')} world="midnight" onclose={() => (quiz = undefined)}>
		<div class="px-6 py-8 sm:p-10">
			<span class="bt-eyebrow text-ink-muted mb-3">{$t('words.analytics')}</span>
			<h2 class="bt-headline text-[26px] sm:text-[34px] break-words pe-10">{@html quiz.title}</h2>
			<dl class="mt-8 grid grid-cols-2 gap-3">
				{#each stats as s}
					<div class="bt-glass bt-glass-faint p-5">
						<dt class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted">{s.label}</dt>
						<dd class="bt-num text-[44px] mt-3">{s.value}</dd>
					</div>
				{/each}
			</dl>
			<p class="mt-6 text-sm text-ink-muted">{$t('dashboard.info_analytics')}</p>
		</div>
	</Modal>
{/if}
