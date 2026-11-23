<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { run } from 'svelte/legacy';

	import type { Question } from '$lib/quiz_types';
	import { ElementTypes, QuizQuestionType } from '$lib/quiz_types';
	import ElementSelection from './slides/element_selection.svelte';
	import SettingsMenu from './slides/settings_menu.svelte';
	import { onMount } from 'svelte';
	import Pikaso from 'pikaso';
	import EditMenu from './slides/edit_menu.svelte';
	import type { Konva, ShapeModel } from 'pikaso';

	interface Props {
		data?: Question;
	}

	let { data = $bindable({
		type: QuizQuestionType.SLIDE,
		time: '120',
		question: '',
		image: undefined,
		answers: ''
	}) }: Props = $props();
	let selected_element = $state(undefined);
	let canvas_el: HTMLDivElement | undefined = $state();
	let canvas: Pikaso;
	let selected_el: null | ShapeModel<Konva.Shape | Konva.Group, Konva.ShapeConfig> = $state(null);

	let elements_binds: Array<HTMLElement> | undefined = [];
	let main_el: undefined | HTMLElement = $state();
	let settings_menu_open = $state(false);

	const set_correct_height = new ResizeObserver((e) => {
		for (const i of e) {
			const id = parseInt(i.target.getAttribute('el_id'));
			data.answers[id].width = i.contentRect.width / main_el.offsetWidth;
			data.answers[id].height = i.contentRect.height / main_el.offsetHeight;
		}
	});

	// the app is dark only: light selection handles on the dark slide surface
	const darkMode = true;
	const add_text_field = () => {
		if (selected_element === ElementTypes.Text) {
			canvas.shapes.label.insert({
				container: {
					x: 40,
					y: 40
				},
				text: {
					text: 'Text',
					fontSize: 24,
					fill: '#feffff',
					fontFamily: "'LOREAL Essentielle', sans-serif"
				}
			});
		} else if (selected_element === ElementTypes.Headline) {
			canvas.shapes.label.insert({
				container: {
					x: 40,
					y: 40
				},
				text: {
					text: 'Headline',
					fontSize: 48,
					fill: '#feffff',
					fontStyle: 'bold',
					fontFamily: "'LOREAL Essentielle', sans-serif"
				}
			});
		} else if (selected_element === ElementTypes.Circle) {
			canvas.shapes.circle.insert({
				x: 40,
				y: 40,
				radius: 50,
				fill: '#5db5df'
			});
		} else if (selected_element === ElementTypes.Rectangle) {
			canvas.shapes.rect.insert({
				x: 40,
				y: 40,
				width: 50,
				height: 50,
				fill: '#5db5df'
			});
		}
	};

	run(() => {
		if (selected_element) {
			add_text_field();
		}
	});
	const assign_resize_handlers = () => {
		for (let i = 0; i < elements_binds.length; i++) {
			set_correct_height.observe(elements_binds[i]);
		}
	};

	/*	if (data.answers.length !== 0) {
			for (let i = 0; i < data.answers.length; i++) {
				data.answers[i].width = data.answers[i].width * main_el.offsetWidth;
				data.answers[i].height = data.answers[i].height * main_el.offsetHeight;
			}
		}*/

	run(() => {
		elements_binds;
		assign_resize_handlers();
	});

	onMount(() => {
		/*		setTimeout(() => {
					for (let i = 0; i < data.answers.length; i++) {
						elements_binds[i].style.height = `${
							data.answers[i].height * main_el.offsetHeight
						}px`;
						elements_binds[i].style.width = `${data.answers[i].width * main_el.offsetWidth}px`;
					}
				}, 200);*/
		canvas = new Pikaso({
			container: canvas_el,
			snapToGrid: {},
			/*			transformer: {
							borderStroke: "#00ff00",
							anchorStroke: "#00ff00"
						},
						cropper: {
							transformer: {
								borderStroke: "#00ff00",
								// anchorFill: "#00ff00",
								anchorStroke: "#00ff00"
							},
							guides: {
								color: "#00ff00"
							}
						},*/
			selection: {
				transformer: {
					borderStroke: darkMode ? '#fff' : '#000000',
					anchorStroke: darkMode ? '#fff' : '#000000'
				}
			}
			/*			selection: {
							interactive: false
						}*/
		});
		if (data.answers) {
			if (typeof data.answers === 'string') {
				canvas.import.json(JSON.parse(data.answers));
			}
		}
		canvas.on('*', () => {
			data.answers = JSON.stringify(canvas.export.toJson());
		});
		canvas.on('selection:change', (data) => {
			/*			data.shapes[0].update({fill: "#ffffff"})
						console.log(data.shapes[0])*/
			// console.log(canvas.board.shapes)
			if (data.shapes.length > 0) {
				selected_el = data.shapes[0];
			} else {
				selected_el = null;
			}
		});
	});
</script>

<div class="relative flex h-full w-full flex-col" bind:this={main_el}>
	<div class="toolbar relative z-40 mx-4 mb-3 grid grid-cols-[auto_1fr_auto] items-start gap-3">
		<div class="relative">
			<button
				class="tbtn"
				class:tbtn-on={settings_menu_open}
				onclick={() => {
					settings_menu_open = !settings_menu_open;
				}}
				type="button"
				aria-expanded={settings_menu_open}
			>
				<svg class="h-5 w-5" stroke-width="2" viewBox="0 0 24 24" fill="none" aria-hidden="true">
					<path d="M12 15a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" />
					<path
						d="M19.622 10.395l-1.097-2.65L20 6l-2-2-1.735 1.483-2.707-1.113L12.935 2h-1.954l-.632 2.401-2.645 1.115L6 4 4 6l1.453 1.789-1.08 2.657L2 11v2l2.401.655L5.516 16.3 4 18l2 2 1.791-1.46 2.606 1.072L11 22h2l.604-2.387 2.651-1.098C16.697 18.831 18 20 18 20l2-2-1.484-1.75 1.098-2.652 2.386-.62V11l-2.378-.605z"
						stroke="currentColor"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				</svg>
				<span>Slide settings</span>
			</button>
			{#if settings_menu_open}
				<div class="absolute top-full left-0 mt-2">
					<SettingsMenu bind:time={data.time} bind:title={data.question} />
				</div>
			{/if}
		</div>
		<div class="flex justify-center">
			<EditMenu {selected_el} />
		</div>
		<div class="relative">
			<button
				class="tbtn tbtn-primary"
				onclick={() => {
					selected_element = selected_element === null ? undefined : null;
				}}
				type="button"
				aria-expanded={selected_element === null}
			>
				<svg class="h-5 w-5" stroke-width="2.5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
					<path d="M12 5v14M5 12h14" stroke="currentColor" stroke-linecap="round" />
				</svg>
				<span>Add element</span>
			</button>
			{#if selected_element === null}
				<div class="absolute top-full right-0 mt-2">
					<ElementSelection bind:selected_element />
				</div>
			{/if}
		</div>
	</div>
	<div class="surface mx-4 mb-4 min-h-0 flex-1">
		<div bind:this={canvas_el} class="block h-full w-full"></div>
	</div>
</div>

<style>
	.tbtn {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		height: 40px;
		padding: 0 16px;
		border-radius: 999px;
		background: var(--fill-glass);
		color: var(--ink);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 2px;
		text-transform: uppercase;
		white-space: nowrap;
	}
	.tbtn:hover,
	.tbtn-on {
		background: var(--fill-glass-strong);
	}
	.tbtn-primary {
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		color: var(--ink-dark);
	}
	.tbtn-primary:hover {
		background: linear-gradient(90deg, var(--accent-sky) 0%, var(--accent-green) 100%);
		filter: brightness(1.08);
	}
	.tbtn:focus-visible {
		outline: 3px solid var(--accent-sky-tint);
		outline-offset: 2px;
	}
	/* the slide itself: the dark ground it is shown on in the game */
	.surface {
		border-radius: 18px;
		overflow: hidden;
		background-color: #170d43;
		background-image:
			linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
			linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
		background-size: 40px 40px;
	}
</style>
