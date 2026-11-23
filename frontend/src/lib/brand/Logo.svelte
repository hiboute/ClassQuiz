<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	The L'Oréal Beauty Tech, India Tech Hub lockup. White on dark grounds (the
	default), black on light grounds. Never under 160px wide.
-->
<script lang="ts">
	interface Props {
		width?: number;
		variant?: 'white' | 'black';
		href?: string;
		class?: string;
	}

	let { width = 160, variant = 'white', href, class: klass = '' }: Props = $props();

	const src = $derived(`/brand/beauty-tech-ith-${variant}.png`);
	const ratio = $derived(variant === 'white' ? 254 / 895 : 283 / 895);
	const alt = "L'Oréal Beauty Tech, India Tech Hub";
</script>

{#if href}
	<a {href} class="inline-block {klass}" aria-label={alt}>
		<img {src} {alt} width={width} height={Math.round(width * ratio)} class="block h-auto" />
	</a>
{:else}
	<img
		{src}
		{alt}
		width={width}
		height={Math.round(width * ratio)}
		class="block h-auto {klass}"
	/>
{/if}
