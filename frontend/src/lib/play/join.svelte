<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE

SPDX-License-Identifier: MPL-2.0
-->

<!--
	Phone join: game PIN (prefilled from ?pin= / the QR code), nickname with a
	counter and a "Random name" helper, inline errors for every refusal the
	server can send. The optional custom field and captcha paths still work
	(captcha is off unless the build enables it).
-->
<script lang="ts">
	import { socket } from '$lib/socket';
	import { onDestroy, onMount } from 'svelte';
	import { browser } from '$app/environment';
	import * as Sentry from '@sentry/browser';
	import Cookies from 'js-cookie';
	import Logo from '$lib/brand/Logo.svelte';
	import PhoneShell from '$lib/play/phone/PhoneShell.svelte';
	import { hcaptcha_site_key, recaptcha_key, sentry_dsn } from '$lib/config';
	import {
		NICKNAME_MAX,
		NICKNAME_MIN,
		cleanNickname,
		nicknameProblem
	} from '$lib/play/phone/phone';

	interface Props {
		game_pin: string;
		game_mode: any;
		username: any;
	}

	let {
		game_pin = $bindable(),
		game_mode = $bindable(),
		username = $bindable()
	}: Props = $props();

	const PIN_LENGTH = 6;
	const MAX_RANDOM = 4; // one draw + 3 rerolls
	const JOIN_TIMEOUT_MS = 9000;

	let custom_field: string | undefined = $state();
	let custom_field_value = $state('');
	let captcha_enabled = $state(false);
	let pin_checked = $state(''); // the PIN the server confirmed
	let pin_checking = $state(false);
	let pin_error = $state('');
	let name_error = $state('');
	let form_error = $state('');
	let joining = $state(false);
	let random_used = $state(0);
	let random_waiting = $state(false);
	let pin_from_link = $state(false);
	let name_input: HTMLInputElement | undefined = $state();
	let host = $state('quiz.indiatechhub.xyz');
	let join_timer: ReturnType<typeof setTimeout> | undefined;

	const hcaptchaSitekey = hcaptcha_site_key;
	let hcaptcha: any = {
		execute: async () => ({ response: '' }),
		render: () => {}
	};
	let hcaptchaWidgetID: any;

	const clean_name = $derived(cleanNickname(username ?? ''));
	const local_problem = $derived(nicknameProblem(username ?? ''));
	const pin_ok = $derived(game_pin.length === PIN_LENGTH && pin_checked === game_pin);
	const can_join = $derived(
		pin_ok &&
			!joining &&
			clean_name.length >= NICKNAME_MIN &&
			clean_name.length <= NICKNAME_MAX &&
			!local_problem &&
			(!custom_field || String(custom_field_value ?? '').trim().length > 0)
	);
	const pin_display = $derived(
		game_pin.length > 3 ? `${game_pin.slice(0, 3)} ${game_pin.slice(3)}` : game_pin
	);

	onMount(() => {
		if (!browser) return;
		host = window.location.host || host;
		pin_from_link = game_pin.length === PIN_LENGTH;
		if (!username) prefetch_username();
		hcaptcha = (window as any).hcaptcha ?? hcaptcha;
		if (hcaptcha?.render && captcha_enabled && hcaptchaSitekey) {
			try {
				hcaptchaWidgetID = hcaptcha.render('hcaptcha', {
					sitekey: hcaptchaSitekey,
					size: 'invisible',
					theme: 'dark'
				});
			} catch {
				/* rendered when the script loads */
			}
		}
	});

	const prefetch_username = async () => {
		try {
			const res = await fetch('/api/v1/users/me');
			if (res.status !== 200) return;
			const json = await res.json();
			if (!username && typeof json.username === 'string') {
				username = json.username.slice(0, NICKNAME_MAX);
			}
		} catch {
			/* not signed in */
		}
	};

	const check_pin = async (pin: string) => {
		pin_checking = true;
		pin_error = '';
		try {
			let api = '';
			try {
				api = (process as any)?.env?.API_URL ?? '';
			} catch {
				api = '';
			}
			const res = await fetch(`${api}/api/v1/quiz/play/check_captcha/${pin}`);
			if (pin !== game_pin) return; // typed on meanwhile
			if (res.status === 404) {
				pin_error = 'No game with this PIN. Check the big screen.';
				pin_checked = '';
				return;
			}
			if (res.status !== 200) {
				pin_error = 'Could not check this PIN. Try again in a moment.';
				pin_checked = '';
				return;
			}
			const json = await res.json();
			game_mode = json.game_mode;
			captcha_enabled = Boolean(json.enabled);
			custom_field = json.custom_field ?? undefined;
			pin_checked = pin;
		} catch {
			if (pin === game_pin) {
				pin_error = 'No connection. Check your network and try again.';
				pin_checked = '';
			}
		} finally {
			if (pin === game_pin) pin_checking = false;
		}
	};

	// Keep only digits, and check the PIN with the server once it is complete
	let last_checked_pin = '';
	$effect(() => {
		const cleaned = (game_pin ?? '').replace(/\D/g, '').slice(0, PIN_LENGTH);
		if (cleaned !== game_pin) {
			game_pin = cleaned;
			return;
		}
		if (cleaned.length === PIN_LENGTH && cleaned !== last_checked_pin) {
			last_checked_pin = cleaned;
			check_pin(cleaned);
		} else if (cleaned.length < PIN_LENGTH) {
			last_checked_pin = '';
			pin_checked = '';
			pin_error = '';
		}
	});

	// The server's answer to a refused nickname replaces the local hint
	$effect(() => {
		void username;
		name_error = '';
		form_error = '';
	});

	const stop_joining = () => {
		joining = false;
		if (join_timer) clearTimeout(join_timer);
		join_timer = undefined;
	};

	const emit_join = (captcha: string | undefined) => {
		socket.emit('join_game', {
			username: clean_name,
			game_pin: game_pin,
			captcha,
			custom_field: custom_field ? String(custom_field_value ?? '').trim() : undefined
		});
	};

	const join = async (e?: Event) => {
		e?.preventDefault();
		if (!can_join) {
			if (local_problem) name_error = local_problem;
			return;
		}
		if (Cookies.get('kicked') === game_pin) {
			name_error = 'You were removed from this game by the host.';
			return;
		}
		username = clean_name;
		form_error = '';
		joining = true;
		join_timer = setTimeout(() => {
			if (joining) {
				joining = false;
				form_error = 'No answer from the server. Check your connection and try again.';
			}
		}, JOIN_TIMEOUT_MS);

		if (captcha_enabled && hcaptchaSitekey && hcaptcha?.execute) {
			try {
				const { response } = await hcaptcha.execute(hcaptchaWidgetID, { async: true });
				emit_join(response);
			} catch (err) {
				if (sentry_dsn) Sentry.captureException(err);
				stop_joining();
				form_error = 'The security check failed. Reload the page and try again.';
			}
		} else if (captcha_enabled && recaptcha_key && (window as any).grecaptcha) {
			const grecaptcha = (window as any).grecaptcha;
			grecaptcha.ready(() => {
				grecaptcha
					.execute(recaptcha_key, { action: 'submit' })
					.then((token: string) => emit_join(token))
					.catch(() => {
						stop_joining();
						form_error = 'The security check failed. Reload the page and try again.';
					});
			});
		} else {
			emit_join(undefined);
		}
	};

	const random_name = () => {
		if (random_used >= MAX_RANDOM || random_waiting) return;
		random_waiting = true;
		random_used += 1;
		socket.emit('get_random_nickname', pin_ok ? { game_pin } : {});
		setTimeout(() => (random_waiting = false), 3000);
	};

	// Server replies
	const on_random = (data: { nickname?: string }) => {
		random_waiting = false;
		if (data?.nickname) {
			username = data.nickname.slice(0, NICKNAME_MAX);
		}
	};
	const on_invalid = (data: { code?: string; message?: string }) => {
		stop_joining();
		name_error = data?.message || 'This nickname is not allowed. Try another one.';
		name_input?.focus();
	};
	const on_banned = (data: { message?: string }) => {
		stop_joining();
		name_error = data?.message || 'This nickname was removed from the game by the host.';
	};
	const on_exists = () => {
		stop_joining();
		name_error = 'Someone already took this nickname. Try another one.';
		name_input?.focus();
	};
	const on_locked = () => {
		stop_joining();
		form_error = 'The host closed this game to new players.';
	};
	const on_not_found = () => {
		stop_joining();
		pin_checked = '';
		pin_error = 'No game with this PIN. Check the big screen.';
	};
	const on_captcha = (data: { message?: string }) => {
		stop_joining();
		form_error = data?.message || 'The security check failed. Try again.';
	};
	const on_joined = () => stop_joining();
	const on_error = () => {
		if (!joining) return;
		stop_joining();
		form_error = 'Something went wrong. Try again.';
	};

	socket.on('random_nickname', on_random);
	socket.on('username_invalid', on_invalid);
	socket.on('username_banned', on_banned);
	socket.on('username_already_exists', on_exists);
	socket.on('game_locked', on_locked);
	socket.on('game_not_found', on_not_found);
	socket.on('captcha_invalid', on_captcha);
	socket.on('joined_game', on_joined);
	socket.on('error', on_error);

	onDestroy(() => {
		stop_joining();
		socket.off('random_nickname', on_random);
		socket.off('username_invalid', on_invalid);
		socket.off('username_banned', on_banned);
		socket.off('username_already_exists', on_exists);
		socket.off('game_locked', on_locked);
		socket.off('game_not_found', on_not_found);
		socket.off('captcha_invalid', on_captcha);
		socket.off('joined_game', on_joined);
		socket.off('error', on_error);
	});
</script>

<svelte:head>
	{#if captcha_enabled && hcaptchaSitekey}
		<script src="https://js.hcaptcha.com/1/api.js" async defer></script>
	{/if}
	{#if recaptcha_key && captcha_enabled}
		<script src="https://www.google.com/recaptcha/api.js?render={recaptcha_key}"></script>
	{/if}
</svelte:head>

<PhoneShell world="indigo" state="join">
	<Logo width={160} />
	<h1 class="pj-title">
		<span class="bt-kicker pj-kicker">Live Quiz</span>
		<span class="bt-headline pj-headline">Ready to play</span>
	</h1>
	<p class="pj-sub">Pick a nickname the room will see on the leaderboard.</p>

	<form class="pj-form" onsubmit={join} novalidate>
		<label class="pj-field" class:pj-field-error={pin_error}>
			<span class="bt-eyebrow">Game PIN</span>
			<input
				class="pj-input pj-pin bt-num"
				data-testid="pin-input"
				bind:value={game_pin}
				inputmode="numeric"
				autocomplete="off"
				pattern="[0-9]*"
				maxlength={PIN_LENGTH}
				placeholder="000 000"
				aria-invalid={pin_error ? 'true' : undefined}
				aria-describedby="pj-pin-hint"
				enterkeyhint="next"
				onkeydown={(e) => {
					if (e.key === 'Enter') {
						e.preventDefault();
						name_input?.focus();
					}
				}}
			/>
			<span class="pj-hint" id="pj-pin-hint" role={pin_error ? 'alert' : undefined}>
				{#if pin_error}
					{pin_error}
				{:else if pin_checking}
					Checking the PIN
				{:else if pin_ok && pin_from_link}
					Filled in from the QR code
				{:else if pin_ok}
					Game found: {pin_display}
				{:else}
					The 6 digits on the big screen
				{/if}
			</span>
		</label>

		<label class="pj-field" class:pj-field-error={name_error}>
			<span class="bt-eyebrow">Nickname</span>
			<input
				class="pj-input pj-name"
				data-testid="nickname-input"
				bind:this={name_input}
				bind:value={username}
				maxlength={NICKNAME_MAX + 4}
				autocomplete="nickname"
				autocapitalize="words"
				spellcheck="false"
				placeholder="Your nickname"
				enterkeyhint="go"
				aria-invalid={name_error ? 'true' : undefined}
				aria-describedby="pj-name-hint"
			/>
			<span class="pj-hint pj-hint-row" id="pj-name-hint">
				{#if name_error}
					<span role="alert">{name_error}</span>
				{:else if local_problem && clean_name.length > 0}
					<span>{local_problem}</span>
				{:else}
					<span>{clean_name.length} of {NICKNAME_MAX} characters</span>
				{/if}
			</span>
		</label>

		{#if custom_field}
			<label class="pj-field">
				<span class="bt-eyebrow">{custom_field}</span>
				<input
					class="pj-input pj-custom"
					data-testid="custom-field-input"
					bind:value={custom_field_value}
					maxlength="60"
				/>
			</label>
		{/if}

		<button
			type="button"
			class="bt-btn-ghost pj-random"
			data-testid="random-name"
			onclick={random_name}
			disabled={random_used >= MAX_RANDOM || random_waiting}
		>
			{#if random_used === 0}
				Random name
			{:else if random_used >= MAX_RANDOM}
				No more random names
			{:else}
				Another random name ({MAX_RANDOM - random_used} left)
			{/if}
		</button>

		{#if form_error}
			<p class="pj-form-error" role="alert">{form_error}</p>
		{/if}

		<button
			type="submit"
			class="bt-btn-primary bt-btn-xl bt-btn-block pj-btn"
			data-testid="join-submit"
			disabled={!can_join}
			aria-busy={joining}
		>
			{joining ? 'Joining' : 'Join'}
		</button>
	</form>

	<p class="pj-foot">Or join at <b>{host}</b></p>
</PhoneShell>
<div
	id="hcaptcha"
	class="h-captcha"
	data-sitekey={hcaptchaSitekey}
	data-size="invisible"
	data-theme="dark"
></div>

<style>
	.pj-title {
		margin: 44px 0 0;
	}
	.pj-kicker {
		font-size: 20px;
	}
	.pj-headline {
		font-size: 44px;
		margin-top: 6px;
	}
	.pj-sub {
		margin: 12px 0 0;
		font-size: 17px;
		color: var(--ink-muted);
	}
	.pj-form {
		margin-top: 28px;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.pj-field {
		display: block;
		border-radius: var(--radius-bt-xl);
		background: var(--fill-glass-mid);
		padding: 14px 20px 14px;
		transition: box-shadow 150ms ease;
	}
	.pj-field:focus-within {
		box-shadow: 0 0 0 3px var(--accent-sky);
	}
	.pj-field-error,
	.pj-field-error:focus-within {
		box-shadow: 0 0 0 3px var(--accent-pink);
	}
	.pj-input {
		display: block;
		width: 100%;
		margin-top: 6px;
		padding: 0;
		border: 0;
		outline: none;
		background: transparent;
		color: var(--ink);
		font-family: inherit;
		caret-color: var(--accent-sky);
	}
	.pj-input::placeholder {
		color: var(--ink-muted);
		opacity: 0.45;
	}
	.pj-pin {
		font-size: 40px;
		letter-spacing: 6px;
		line-height: 1.1;
		height: 46px;
	}
	.pj-name {
		font-size: 26px;
		font-weight: 700;
		line-height: 1.2;
		height: 34px;
	}
	.pj-custom {
		font-size: 20px;
		font-weight: 700;
		height: 30px;
	}
	.pj-hint {
		display: block;
		min-height: 18px;
		margin-top: 4px;
		font-size: 14px;
		line-height: 18px;
		color: var(--ink-muted);
	}
	.pj-field-error .pj-hint {
		color: var(--accent-orchid-tint);
	}
	.pj-random {
		align-self: flex-start;
		min-height: 44px;
		padding: 0 20px;
		font-size: 13px;
		letter-spacing: 2px;
	}
	.pj-form-error {
		margin: 0;
		padding: 12px 16px;
		border-radius: var(--radius-bt-lg);
		background: var(--fill-deep);
		color: var(--accent-orchid-tint);
		font-size: 15px;
	}
	.pj-btn {
		margin-top: 10px;
	}
	@media (max-height: 760px) {
		.pj-title {
			margin-top: 22px;
		}
		.pj-headline {
			font-size: 38px;
		}
		.pj-sub {
			font-size: 15px;
		}
		.pj-form {
			margin-top: 18px;
			gap: 10px;
		}
	}
	.pj-foot {
		margin: auto 0 0;
		padding-top: 20px;
		text-align: center;
		font-size: 15px;
		color: var(--ink-muted);
	}
	.pj-foot b {
		color: var(--ink);
		font-weight: 700;
	}
</style>
