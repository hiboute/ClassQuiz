<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Save state of the phone editor: ready, saving, or what blocks the save. -->
<script lang="ts">
	import EdIcon from '$lib/editor/EdIcon.svelte';

	interface Props {
		tone: 'bad' | 'ok' | 'busy';
		label: string;
		center?: boolean;
	}

	let { tone, label, center = false }: Props = $props();
</script>

<span
	class="state"
	class:state-bad={tone === 'bad'}
	class:state-busy={tone === 'busy'}
	class:justify-center={center}
	aria-live="polite"
>
	<EdIcon name={tone === 'bad' ? 'warn' : 'cloud'} size={17} />
	<span class="truncate">{label}</span>
</span>

<style>
	.state {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
		font-size: 14px;
		font-weight: 700;
		color: var(--accent-green-tint);
	}
	.state-bad {
		color: var(--accent-orchid-tint);
	}
	.state-busy {
		color: var(--ink);
	}
</style>
