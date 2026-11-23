<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { ElementTypes } from '$lib/quiz_types';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	let { selected_element = $bindable() } = $props();
	const keybinding_list = {
		t: ElementTypes.Text,
		h: ElementTypes.Headline,
		r: ElementTypes.Rectangle,
		c: ElementTypes.Circle
		// "i": ElementTypes.Image
	};

	const keypress_listener = (key: KeyboardEvent) => {
		if (selected_element !== null) {
			return;
		}
		const sel_type = keybinding_list[key.key];
		if (sel_type) {
			selected_element = sel_type;
		} else if (key.code === 'Escape') {
			selected_element = undefined;
		}
	};

	onMount(() => {
		document.body.addEventListener('keydown', keypress_listener);
	});
	const element_list: Array<{
		name: string;
		description: string;
		type: ElementTypes;
		icon: string | undefined;
		shortcut: string;
	}> = [
		{
			name: $t('editor.slide.headline'),
			description: $t('editor.slide.headline_description'),
			type: ElementTypes.Headline,
			icon: undefined,
			shortcut: 'h'
		},
		{
			name: $t('editor.slide.text'),
			description: $t('editor.slide.text_description'),
			type: ElementTypes.Text,
			icon: undefined,
			shortcut: 't'
		},
		{
			name: $t('editor.slide.rectangle'),
			description: $t('editor.slide.rectangle_description'),
			type: ElementTypes.Rectangle,
			icon: undefined,
			shortcut: 'r'
		},
		{
			name: 'Circle',
			description: 'A filled circle',
			type: ElementTypes.Circle,
			icon: undefined,
			shortcut: 'c'
		}
	];
</script>

<div class="pop flex w-72 flex-col p-2" transition:fade|global={{ duration: 100 }}>
	<ul class="flex flex-col gap-1">
		{#each element_list as el}
			<li>
				<button
					type="button"
					class="item"
					onclick={() => {
						selected_element = el.type;
					}}
				>
					<span class="min-w-0 flex-1">
						<span class="block font-black uppercase tracking-[1px]">{el.name}</span>
						<span class="block text-xs text-ink-muted">{el.description}</span>
					</span>
					<kbd>{el.shortcut}</kbd>
				</button>
			</li>
		{/each}
	</ul>
</div>

<style>
	.pop {
		border-radius: 18px;
		background: rgba(14, 10, 46, 0.95);
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
	}
	.item {
		display: flex;
		align-items: center;
		gap: 10px;
		width: 100%;
		padding: 10px 12px;
		border-radius: 12px;
		text-align: left;
	}
	.item:hover,
	.item:focus-visible {
		background: var(--fill-glass-mid);
		outline: none;
	}
	kbd {
		display: grid;
		place-items: center;
		width: 26px;
		height: 26px;
		border-radius: 8px;
		background: var(--fill-glass-mid);
		font-family: var(--bt-font);
		font-size: 12px;
		text-transform: uppercase;
	}
</style>
