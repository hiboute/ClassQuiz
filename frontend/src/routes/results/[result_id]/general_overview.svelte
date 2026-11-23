<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	interface Props {
		scores: { [key: string]: string | number };
		answers: { username: string; right: boolean }[][];
		questions: unknown[];
	}

	let { scores, answers, questions }: Props = $props();

	const ranking = $derived(
		Object.entries(scores)
			.map(([name, s]) => ({ name, score: Number(s) || 0 }))
			.sort((a, b) => b.score - a.score)
	);
	const average = $derived(
		ranking.length ? Math.round(ranking.reduce((n, r) => n + r.score, 0) / ranking.length) : 0
	);
	const accuracy = $derived.by(() => {
		let total = 0;
		let right = 0;
		for (const q of answers ?? []) {
			for (const a of q ?? []) {
				total++;
				if (a.right) right++;
			}
		}
		return total ? Math.round((right / total) * 100) : 0;
	});
	const stats = $derived([
		{ label: 'Players', value: ranking.length },
		{ label: 'Questions', value: questions.length },
		{ label: 'Average score', value: average },
		{ label: 'Right answers', value: `${accuracy}%` }
	]);
</script>

<dl class="grid grid-cols-2 lg:grid-cols-4 gap-3">
	{#each stats as s}
		<div class="bt-glass bt-glass-faint p-5 sm:p-6">
			<dt class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted">{s.label}</dt>
			<dd class="bt-num text-[40px] sm:text-[52px] mt-4">{s.value}</dd>
		</div>
	{/each}
</dl>

{#if ranking.length}
	<section class="bt-glass bt-glass-faint mt-4 p-5 sm:p-7">
		<span class="bt-eyebrow text-ink-muted mb-4">Top {Math.min(10, ranking.length)}</span>
		<ol class="flex flex-col gap-1.5">
			{#each ranking.slice(0, 10) as r, i}
				<li
					class="flex items-center gap-4 rounded-[14px] px-4 py-3"
					style={i < 3 ? 'background: rgba(255,255,255,0.10)' : 'background: rgba(255,255,255,0.04)'}
				>
					<span class="bt-num text-2xl w-8 text-ink-muted">{i + 1}</span>
					<span class="flex-1 min-w-0 truncate font-bold">{r.name}</span>
					<span class="bt-num text-2xl">{r.score}</span>
				</li>
			{/each}
		</ol>
	</section>
{/if}
