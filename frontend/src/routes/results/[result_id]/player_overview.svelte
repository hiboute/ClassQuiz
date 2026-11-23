<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	interface Props {
		scores: { [key: string]: string };
		custom_field: { [key: string]: string };
		answers: any[][];
	}

	let { scores, custom_field, answers }: Props = $props();

	let usernames = $derived(
		Object.keys(scores).sort((a, b) => (parseFloat(scores[b]) || 0) - (parseFloat(scores[a]) || 0))
	);

	const correctCounts = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const questionAnswers of answers ?? []) {
			for (const answer of questionAnswers ?? []) {
				counts[answer.username] = (counts[answer.username] ?? 0) + (answer.right ? 1 : 0);
			}
		}
		return counts;
	});
	const has_custom = $derived(Object.keys(custom_field ?? {}).length !== 0);
	let filter = $state('');
	const shown = $derived(
		filter.trim()
			? usernames.filter((u) => u.toLowerCase().includes(filter.trim().toLowerCase()))
			: usernames
	);
</script>

<section class="bt-glass bt-glass-faint p-4 sm:p-7">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<span class="bt-eyebrow text-ink-muted">{usernames.length} players</span>
		<input
			type="search"
			bind:value={filter}
			placeholder="Find a player"
			aria-label="Find a player"
			class="bt-input !text-sm !py-2.5 !px-4 max-w-56"
		/>
	</div>
	<div class="mt-4 overflow-x-auto -mx-2">
		<table class="min-w-full text-sm">
			<thead>
				<tr class="text-ink-muted">
					<th class="px-2 py-2 text-start font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]">#</th>
					<th class="px-2 py-2 text-start font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
						>{$t('result_page.player_name')}</th
					>
					<th class="px-2 py-2 text-end font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
						>{$t('result_page.player_correct_questions')}</th
					>
					<th class="px-2 py-2 text-end font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
						>{$t('result_page.player_score')}</th
					>
					{#if has_custom}
						<th class="px-2 py-2 text-start font-normal whitespace-nowrap uppercase text-[11px] tracking-[2px]"
							>{$t('result_page.custom_field')}</th
						>
					{/if}
				</tr>
			</thead>
			<tbody>
				{#each shown as uname}
					<tr class="border-t border-white/10">
						<td class="px-2 py-3 tabular-nums text-ink-muted">{usernames.indexOf(uname) + 1}</td>
						<td class="px-2 py-3 font-bold">{uname}</td>
						<td class="px-2 py-3 text-end tabular-nums">{correctCounts[uname] ?? 0}</td>
						<td class="px-2 py-3 text-end tabular-nums font-black">{scores[uname]}</td>
						{#if has_custom}
							<td class="px-2 py-3">{custom_field[uname] ?? ''}</td>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</section>
