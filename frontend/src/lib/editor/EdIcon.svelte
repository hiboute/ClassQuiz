<!--
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!-- Stroke icons of the quiz editor (24px grid, currentColor). -->
<script lang="ts">
	type Name =
		| 'plus'
		| 'trash'
		| 'up'
		| 'down'
		| 'check'
		| 'x'
		| 'image'
		| 'clock'
		| 'copy'
		| 'globe'
		| 'lock'
		| 'save'
		| 'warn'
		| 'cloud'
		| 'slide'
		| 'settings'
		| 'palette'
		| 'search'
		| 'video'
		| 'folder';

	interface Props {
		name: Name;
		size?: number;
		class?: string;
		stroke?: number;
	}

	let { name, size = 20, class: klass = '', stroke = 2 }: Props = $props();

	const PATHS: Record<Name, string[]> = {
		plus: ['M12 5v14', 'M5 12h14'],
		trash: [
			'M4 7h16',
			'M10 11v6',
			'M14 11v6',
			'M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12',
			'M9 7V4h6v3'
		],
		up: ['M6 15l6-6 6 6'],
		down: ['M6 9l6 6 6-6'],
		check: ['M5 12.5l4.5 4.5L19 7.5'],
		x: ['M6 6l12 12', 'M18 6L6 18'],
		image: [
			'M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z',
			'M4 16l4.5-4.5a2 2 0 0 1 2.8 0L16 16',
			'M14 14l1.5-1.5a2 2 0 0 1 2.8 0L20 14',
			'M14.5 8.5h.01'
		],
		clock: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 7.5V12l3 2'],
		copy: [
			'M9 9h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V10a1 1 0 0 1 1-1z',
			'M16 9V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3'
		],
		globe: [
			'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z',
			'M3.5 9h17',
			'M3.5 15h17',
			'M12 3c2.5 2.7 3.5 5.7 3.5 9s-1 6.3-3.5 9c-2.5-2.7-3.5-5.7-3.5-9s1-6.3 3.5-9z'
		],
		lock: ['M6 11h12v9H6z', 'M8.5 11V8a3.5 3.5 0 0 1 7 0v3'],
		save: ['M12 4v11', 'M7.5 10.5L12 15l4.5-4.5', 'M5 19h14'],
		warn: ['M12 4l9 16H3z', 'M12 10v4', 'M12 17h.01'],
		cloud: [
			'M7 18h10.5a4 4 0 0 0 .6-7.96A6 6 0 0 0 6.4 9.1 4.5 4.5 0 0 0 7 18z'
		],
		slide: ['M4 5h16v11H4z', 'M9 20h6', 'M12 16v4'],
		settings: [
			'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
			'M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z'
		],
		palette: [
			'M12 21a9 9 0 1 1 9-9c0 2.5-2 3.5-4 3.5h-1.5a1.5 1.5 0 0 0-1 2.6c.6.6.4 2.9-2.5 2.9z',
			'M7.5 11.5h.01',
			'M10.5 7.5h.01',
			'M15 8h.01'
		],
		search: ['M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z', 'M20 20l-4-4'],
		video: ['M4 7h11v10H4z', 'M15 10.5l5-3v9l-5-3'],
		folder: ['M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z']
	};
</script>

<svg
	viewBox="0 0 24 24"
	width={size}
	height={size}
	fill="none"
	stroke="currentColor"
	stroke-width={stroke}
	stroke-linecap="round"
	stroke-linejoin="round"
	class={klass}
	style="flex:none"
	aria-hidden="true"
>
	{#each PATHS[name] as d}
		<path {d} />
	{/each}
</svg>
