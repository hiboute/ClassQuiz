<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Small ring loader for the editor (ink on dark grounds). -->
<script lang="ts">
	interface Props {
		label?: string;
		class?: string;
	}
	let { label = 'Loading', class: klass = '' }: Props = $props();
</script>

<div class="flex items-center justify-center gap-3 py-6 text-ink-muted {klass}" role="status">
	<svg class="h-6 w-6 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
		<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-opacity="0.25" stroke-width="3" />
		<path d="M21 12a9 9 0 0 0-9-9" fill="none" stroke="var(--accent-sky)" stroke-width="3" stroke-linecap="round" />
	</svg>
	<span class="bt-eyebrow text-[11px]">{label}</span>
</div>
