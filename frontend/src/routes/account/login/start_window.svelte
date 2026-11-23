<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<!--
	First login step: email or username and password on one form. The server
	flow stays two-step: /login/start returns the allowed methods, then the
	password goes to /login/step/1. If the account has no password, or needs a
	second factor, the page moves on to the method picker.
-->
<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { registration_disabled } from '$lib/config';
	import OAuthBlock from './oauth_block.svelte';

	let {
		session_data = $bindable({}),
		step = $bindable(),
		selected_method = $bindable(),
		done = $bindable()
	} = $props();

	const { t } = getLocalization();
	// VITE_REGISTRATION_DISABLED is a string: anything but empty or "false" turns sign-up off.
	const sign_up_open = !registration_disabled;
	let email = $state('');
	let password = $state('');
	let isSubmitting = $state(false);
	let error = $state('');
	const can_submit = $derived(email.trim() !== '' && password !== '' && !isSubmitting);

	const start_login = async (e: Event): Promise<void> => {
		e.preventDefault();
		if (!can_submit) {
			return;
		}
		isSubmitting = true;
		error = '';
		try {
			const res = await fetch('/api/v1/login/start', {
				method: 'post',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email: email.trim() })
			});
			if (!res.ok) {
				error = 'No account matches this email or username.';
				isSubmitting = false;
				return;
			}
			const data = await res.json();
			if (!Array.isArray(data.step_1) || !data.step_1.includes('PASSWORD')) {
				// No password on this account (passkey only): use the method picker.
				session_data = data;
				step = 1;
				return;
			}
			const res2 = await fetch(`/api/v1/login/step/1?session_id=${data.session_id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ auth_type: 'PASSWORD', data: password })
			});
			if (res2.status === 200) {
				done = true;
				window.location.reload();
				return;
			}
			if (res2.status === 202) {
				// Second factor needed.
				session_data = data;
				selected_method = null;
				step = 2;
				return;
			}
			error = 'Wrong email, username or password.';
			password = '';
		} catch {
			error = 'The server could not be reached. Try again.';
		}
		isSubmitting = false;
	};
</script>

<div class="p-6 sm:p-8">
	<span class="bt-eyebrow text-ink-muted mb-3">Organisers</span>
	<h2 class="bt-headline text-[28px] sm:text-[34px]">Sign in</h2>

	<form onsubmit={start_login} class="mt-6 flex flex-col gap-4">
		<div>
			<label for="email" class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted mb-2"
				>{$t('login_page.email_or_username')}</label
			>
			<input
				id="email"
				bind:value={email}
				name="email"
				type="text"
				class="bt-input"
				autocomplete="username"
				autocapitalize="none"
				spellcheck="false"
				required
			/>
		</div>
		<div>
			<label for="password" class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted mb-2"
				>{$t('words.password')}</label
			>
			<input
				id="password"
				bind:value={password}
				name="password"
				type="password"
				class="bt-input"
				autocomplete="current-password"
				required
			/>
		</div>

		{#if error}
			<p class="rounded-[18px] bg-[#ff4d6d]/20 px-4 py-3 text-sm" role="alert">{error}</p>
		{/if}

		<button class="bt-btn-primary bt-btn-block bt-btn-lg mt-2" disabled={!can_submit} type="submit">
			{#if isSubmitting}
				<svg class="h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true"
					><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-opacity=".25" stroke-width="3" /><path
						d="M21 12a9 9 0 0 0-9-9"
						stroke="currentColor"
						stroke-width="3"
						stroke-linecap="round"
					/></svg
				>
				<span class="sr-only">Signing in</span>
			{:else}
				Sign in
			{/if}
		</button>

		<div class="flex flex-wrap items-center justify-between gap-2 text-sm">
			<a
				href="/account/reset-password"
				class="text-ink-muted hover:text-ink underline-offset-4 hover:underline"
				>{$t('register_page.forgot_password?')}</a
			>
			{#if sign_up_open}
				<a
					href="/account/register"
					class="text-ink-muted hover:text-ink underline-offset-4 hover:underline"
					>Create an organiser account</a
				>
			{/if}
		</div>
		<OAuthBlock />
	</form>
</div>
