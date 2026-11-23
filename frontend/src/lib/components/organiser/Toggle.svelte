<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Switch row on glass: label, optional hint, and a pill switch. -->
<script lang="ts">
	interface Props {
		checked?: boolean;
		label: string;
		hint?: string;
		id: string;
		disabled?: boolean;
	}

	let { checked = $bindable(false), label, hint, id, disabled = false }: Props = $props();
</script>

<label
	for={id}
	class="flex items-center justify-between gap-4 rounded-[18px] bg-white/[0.06] px-5 py-4 cursor-pointer hover:bg-white/[0.1] transition-colors"
	class:opacity-50={disabled}
	class:pointer-events-none={disabled}
>
	<span class="min-w-0">
		<span class="block font-bold text-base text-ink">{label}</span>
		{#if hint}
			<span class="block text-sm text-ink-muted mt-0.5">{hint}</span>
		{/if}
	</span>
	<input type="checkbox" {id} bind:checked {disabled} class="peer sr-only" />
	<span
		aria-hidden="true"
		class="relative shrink-0 h-8 w-14 rounded-full bg-white/20 transition-colors
		peer-checked:bg-[linear-gradient(90deg,var(--accent-sky),var(--accent-green))]
		peer-focus-visible:outline peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-[var(--accent-sky-tint)]
		after:content-[''] after:absolute after:top-1 after:start-1 after:h-6 after:w-6 after:rounded-full after:bg-[var(--ink)] after:transition-transform
		peer-checked:after:translate-x-6 rtl:peer-checked:after:-translate-x-6"
	></span>
</label>
