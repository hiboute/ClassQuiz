<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { alertModal } from '$lib/stores';
	import { navbarVisible } from '$lib/stores.svelte';
	import { fade } from 'svelte/transition';
	import Footer from '$lib/footer.svelte';
	import World from '$lib/brand/World.svelte';
	import VerifiedBadge from './verified_badge.svelte';
	import StartWindow from './start_window.svelte';
	import SelectMethod from './select_method.svelte';
	import PasswordComponent from './password_component.svelte';
	import WebauthnComponent from './webauthn_component.svelte';
	import BackupComponent from './backup_component.svelte';
	import TotpComponent from './totp_component.svelte';
	import { browserSupportsWebAuthn } from '@simplewebauthn/browser';

	navbarVisible.visible = true;

	let { data } = $props();
	let { verified } = data;

	let session_data: any = $state({});
	let step = $state(0);
	let selected_method = $state(null);
	let done = $state(false);

	const redirect_back = (done_var: boolean) => {
		if (done_var) {
			setTimeout(() => {
				window.location.reload();
			}, 100);
		}
	};
	let alertModalOpen = false;
	$effect(() => {
		redirect_back(done);
	});

	alertModal.subscribe((data) => {
		if (!alertModalOpen && data.open) {
			alertModalOpen = true;
		}
		if (alertModalOpen && !data.open) {
			window.location.reload();
		}
	});

	const check_auto = (stp: number) => {
		if (stp === 1) {
			if (!browserSupportsWebAuthn()) {
				for (let i = 0; i < session_data.step_1.length; i++) {
					if (session_data.step_1[i] === 'PASSKEY') {
						session_data.step_1.splice(i, 1);
					}
				}
				session_data.step_1 = session_data.step_1;
			}
			if (session_data.step_1.length === 1) {
				selected_method = session_data.step_1[0];
			}
		}
		if (stp === 2) {
			if (!browserSupportsWebAuthn()) {
				for (let i = 0; i < session_data.step_2.length; i++) {
					if (session_data.step_2[i] === 'PASSKEY') {
						session_data.step_2.splice(i, 1);
					}
				}
				session_data.step_2 = session_data.step_2;
			}
			if (session_data.step_2.length === 1) {
				selected_method = session_data.step_2[0];
			}
		}
	};
	$effect(() => check_auto(step));
</script>

<svelte:head>
	<title>Sign in - India Tech Hub Live Quiz</title>
</svelte:head>
<World world="indigo" mesh fullscreen={false} class="min-h-[calc(100dvh-4rem)] flex flex-col">
	<div
		class="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-10 py-10 lg:py-16 grid gap-10 lg:grid-cols-[1fr_minmax(0,440px)] lg:items-center"
	>
		<div class="max-w-xl">
			<span class="bt-eyebrow text-ink-muted mb-5">India Tech Hub Live Quiz</span>
			<span class="bt-kicker text-xl lg:text-[28px]">Host the room</span>
			<h1 class="bt-headline text-[40px] lg:text-[64px] bt-text-display">From one screen</h1>
			<p class="mt-5 text-ink-muted text-base lg:text-lg max-w-md">
				Sign in to write quizzes, start live games and read the results. Players never need an
				account: they join with the game PIN.
			</p>
		</div>

		<div class="w-full max-w-md lg:max-w-none mx-auto lg:mx-0">
			{#if verified}
				<div class="mb-4"><VerifiedBadge /></div>
			{/if}
			<div class="bt-glass overflow-hidden">
				{#key `${step}-${selected_method}`}
					<div in:fade={{ duration: 150 }}>
						{#if step === 0}
							<StartWindow bind:session_data bind:step bind:selected_method bind:done />
						{:else if selected_method === null}
							<SelectMethod {session_data} {step} bind:selected_method />
						{:else if selected_method === 'PASSWORD'}
							<PasswordComponent {session_data} bind:done bind:step bind:selected_method />
						{:else if selected_method === 'PASSKEY'}
							<WebauthnComponent {session_data} bind:done bind:step bind:selected_method />
						{:else if selected_method === 'BACKUP'}
							<BackupComponent {session_data} bind:done bind:step bind:selected_method />
						{:else if selected_method === 'TOTP'}
							<TotpComponent {session_data} bind:done bind:step bind:selected_method />
						{/if}
					</div>
				{/key}
			</div>
		</div>
	</div>
	<Footer />
</World>
