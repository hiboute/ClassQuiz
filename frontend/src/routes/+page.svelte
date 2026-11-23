<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import Footer from '$lib/footer.svelte';
	import World from '$lib/brand/World.svelte';
	import Logo from '$lib/brand/Logo.svelte';

	const description =
		'Join the India Tech Hub live quiz with your game PIN, answer against the clock and climb the leaderboard.';
	const site = 'https://quiz.indiatechhub.xyz';
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz</title>
	<meta name="description" content={description} />

	<meta property="og:url" content="{site}/" />
	<meta property="og:type" content="website" />
	<meta property="og:title" content="India Tech Hub Live Quiz" />
	<meta property="og:description" content={description} />
	<meta property="og:image" content="{site}/brand/og.jpg" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="India Tech Hub Live Quiz" />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image" content="{site}/brand/og.jpg" />
</svelte:head>

<World world="indigo" mesh class="flex flex-col">
	<header class="px-5 pt-7 sm:px-12 sm:pt-10 lg:px-[84px]">
		<Logo width={180} />
	</header>

	<main
		class="flex flex-1 flex-col justify-center px-5 pb-10 pt-14 sm:px-12 lg:px-[84px] max-w-5xl"
	>
		<span class="bt-eyebrow sm:text-[21px] sm:tracking-[6px] text-ink-muted">Beauty Tech trivia</span>
		<h1 class="mt-5">
			<span class="bt-kicker text-2xl sm:text-4xl">India Tech Hub</span>
			<span class="bt-headline bt-text-aurora text-6xl sm:text-8xl lg:text-[120px] mt-1"
				>Live quiz</span
			>
		</h1>
		<p class="mt-6 max-w-xl text-lg sm:text-xl text-ink-muted leading-snug">
			Scan the QR code on the big screen or enter the game PIN. Answer fast, climb the
			leaderboard.
		</p>

		<div class="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
			<a href="/play" class="bt-btn-primary bt-btn-xl w-full sm:w-auto sm:min-w-[320px]"
				>Join a game</a
			>
			<a
				href="/account/login?returnTo=/dashboard"
				class="bt-btn-ghost bt-btn-xl w-full sm:w-auto sm:min-w-[200px]">Host</a
			>
		</div>
	</main>

	<Footer />
</World>
