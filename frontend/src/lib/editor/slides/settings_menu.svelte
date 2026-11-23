<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { fade } from 'svelte/transition';

	let { title = $bindable(), time = $bindable() } = $props();
	if (!time) {
		time = '120';
	}
</script>

<div class="pop flex w-80 flex-col gap-3 p-4" transition:fade|global={{ duration: 100 }}>
	<label class="flex flex-col gap-2">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Name in the list</span>
		<input bind:value={title} type="text" class="bt-input field" />
	</label>
	<label class="flex flex-col gap-2">
		<span class="bt-eyebrow text-[10px] text-ink-muted">Shown for, in seconds</span>
		<input
			value={time}
			oninput={(e) => (time = e.currentTarget.value.replace(/[^0-9]/g, '').slice(0, 3))}
			type="number"
			min="1"
			max="999"
			class="bt-input field w-28"
		/>
	</label>
</div>

<style>
	.pop {
		border-radius: 18px;
		background: rgba(14, 10, 46, 0.95);
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
	}
	.field {
		padding: 10px 14px;
		border-radius: 12px;
		font-size: 16px;
	}
</style>
