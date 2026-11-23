<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { signedIn, pathname } from '$lib/stores';
	import { beforeNavigate } from '$app/navigation';
	import { draw, slide } from 'svelte/transition';
	import { registration_disabled } from './config';
	import Logo from '$lib/brand/Logo.svelte';

	const { t } = getLocalization();

	let menuIsClosed = $state(true);
	const toggleMenu = () => {
		menuIsClosed = !menuIsClosed;
	};

	beforeNavigate(() => {
		menuIsClosed = true; // Closes menu to let the user see the page beneath
	});
</script>

<nav
	class="w-screen px-4 lg:px-10 h-16 fixed top-0 z-30 flex flex-col justify-center bg-[#090924]/75 backdrop-blur-xl text-ink"
>
	<!-- Desktop navbar -->
	<div class="hidden lg:flex lg:items-center lg:flex-row lg:justify-between">
		<div class="lg:flex lg:items-center lg:flex-row gap-2">
			<Logo href="/" width={160} class="mr-6" />
			<a class="bt-btn-primary !min-h-9 !px-5 !text-sm !tracking-[3px]" href="/play"
				>{$t('words.play')}</a
			>
			<a class="btn-nav" href="/explore">{$t('words.explore')}</a>
			<a class="btn-nav" href="/search">{$t('words.search')}</a>
			{#if $signedIn}
				<a class="btn-nav" href="/dashboard">{$t('words.dashboard')}</a>
			{/if}
		</div>
		<div class="lg:flex lg:items-center lg:flex-row gap-1">
			{#if $signedIn}
				<a class="btn-nav" href="/api/v1/users/logout">{$t('words.logout')}</a>
			{:else}
				{#if !registration_disabled}
					<a class="btn-nav" href="/account/register">{$t('words.register')}</a>
				{/if}

				<a
					class="bt-btn-ghost !min-h-9 !px-5 !text-sm"
					href="/account/login?returnTo={$pathname}">{$t('words.login')}</a
				>
			{/if}
		</div>
	</div>

	<!-- Mobile navbar -->
	<div class="lg:hidden">
		<!-- Navbar header -->
		<div class="flex items-center justify-between">
			<Logo href="/" width={160} />

			<div class="flex items-center gap-2">
				<a class="bt-btn-primary !min-h-9 !px-4 !text-sm !tracking-[3px]" href="/play"
					>{$t('words.play')}</a
				>
				{#if menuIsClosed}
					<button
						class="px-2 py-2 text-ink"
						id="open-menu"
						onclick={toggleMenu}
						aria-label="Open navbar"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M3 6h18M3 12h18M3 18h18" />
						</svg>
					</button>
				{:else}
					<button
						class="px-2 py-2 text-ink"
						id="close-menu"
						onclick={toggleMenu}
						aria-label="Close navbar"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><path in:draw|global={{ duration: 300 }} d="M18 6 6 18" /><path
								in:draw|global={{ duration: 300 }}
								d="m6 6 12 12"
							/></svg
						>
					</button>
				{/if}
			</div>
		</div>
	</div>
	<!-- Mobile navbar content -->
	{#if !menuIsClosed}
		<div
			class="lg:hidden absolute left-0 right-0 top-16 flex flex-col gap-1 px-4 pb-4 pt-2 bg-[#090924]/95 backdrop-blur-xl"
			transition:slide|global={{ duration: 300 }}
		>
			<a class="btn-nav" href="/explore">{$t('words.explore')}</a>
			<a class="btn-nav" href="/search">{$t('words.search')}</a>
			{#if $signedIn}
				<a class="btn-nav" href="/dashboard">{$t('words.dashboard')}</a>
				<a class="btn-nav" href="/api/v1/users/logout">{$t('words.logout')}</a>
			{:else}
				{#if !registration_disabled}
					<a class="btn-nav" href="/account/register">{$t('words.register')}</a>
				{/if}
				<a class="btn-nav" href="/account/login?returnTo={$pathname}">{$t('words.login')}</a>
			{/if}
		</div>
	{/if}
</nav>
