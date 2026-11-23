<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	interface Props {
		disabled?: boolean;
		flex?: boolean;
		href?: undefined | string;
		target?: undefined | string;
		type?: 'button' | 'submit' | 'reset';
		children?: import('svelte').Snippet;
		onclick?: (event: MouseEvent) => void;
	}

	let {
		disabled = false,
		flex = false,
		href = undefined,
		target = '_self',
		type = 'button',
		children,
		onclick
	}: Props = $props();
</script>

{#if href}
	<a
		{href}
		{target}
		aria-disabled={disabled}
		class:opacity-50={disabled}
		class:cursor-not-allowed={disabled}
		class:pointer-events-none={disabled}
		class="bt-btn-primary w-full px-4 py-2 tracking-[1.5px] text-sm whitespace-normal leading-tight"
		{onclick}
		class:flex
		class:justify-center={flex}
	>
		{@render children?.()}
	</a>
{:else}
	<button
		{disabled}
		{type}
		class="bt-btn-primary w-full px-4 py-2 tracking-[1.5px] text-sm whitespace-normal leading-tight"
		{onclick}
		class:flex
		class:justify-center={flex}
	>
		{@render children?.()}
	</button>
{/if}
