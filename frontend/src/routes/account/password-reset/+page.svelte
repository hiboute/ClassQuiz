<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';

	const { t } = getLocalization();
	let { data } = $props();
	let { token: string } = data;
	let isSubmitting = $state(false);
	interface PasswordData {
		password1: string;
		password2: string;
	}
	let passwordData: PasswordData = $state({
		password1: '',
		password2: ''
	});
	let passwordsValid = $derived(
		passwordData.password1 === passwordData.password2 && passwordData.password1.length >= 8
	);

	const submit = async (e: Event) => {
		e.preventDefault();
		if (!passwordsValid) {
			return;
		}
		isSubmitting = true;
		const response = await fetch('/api/v1/users/reset-password', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				password: passwordData.password1,
				token
			})
		});
		const data = await response.json();
		if (response.status === 200) {
			window.location.assign('/account/login');
		} else {
			alert(data.detail);
		}
		isSubmitting = false;
	};
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz - Reset your Password</title>
</svelte:head>

<div class="flex items-center justify-center min-h-[calc(100dvh-4rem)] px-4 py-10">
	<div>
		<div
			class="bt-glass w-full max-w-md mx-auto overflow-hidden"
		>
			<div class="p-6 sm:p-8">
				<span class="bt-eyebrow text-ink-muted mb-3">Account</span>
				<h2 class="bt-headline text-[28px] sm:text-[34px]">New password</h2>

				<!--
								<h3 class='mt-2 text-lg font-bold'>
								</h3>
				-->

				<p class="mt-1 text-ink-muted">
					{$t('password_reset_page.reset_password')}
				</p>

				<form onsubmit={submit}>
					<div class="w-full mt-4">
						<div class="pt-4">
							<div class="flex flex-col-reverse gap-2">
								<input
									id="password1"
									bind:value={passwordData.password1}
									name="password1"
									type="password"
									class="bt-input"
									placeholder={$t('words.password')}
								/>
								<label
									for="password1"
									class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
								>
									{$t('words.password')}
								</label>
							</div>
						</div>
						<div class="pt-4">
							<div class="flex flex-col-reverse gap-2">
								<input
									id="password2"
									name="password2"
									type="password"
									bind:value={passwordData.password2}
									class="bt-input"
									placeholder={$t('words.repeat_password')}
								/>
								<label
									for="password2"
									class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
								>
									{$t('words.repeat_password')}
								</label>
							</div>
						</div>

						<div class="flex flex-wrap items-center justify-between gap-3 mt-6">
							<a
								href="/account/login"
								class="text-sm text-ink-muted hover:text-ink hover:underline underline-offset-4"
								>{$t('register_page.already_have_account?')}</a
							>

							<button
								class="bt-btn-primary"
								disabled={!passwordsValid}
								type="submit"
							>
								{#if isSubmitting}
									<svg class="h-4 w-4 animate-spin mx-auto" viewBox="3 3 18 18">
										<path
											class="fill-current opacity-25"
											d="M12 5C8.13401 5 5 8.13401 5 12C5 15.866 8.13401 19 12 19C15.866 19 19 15.866 19 12C19 8.13401 15.866 5 12 5ZM3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12Z"
										/>
										<path
											class="fill-current"
											d="M16.9497 7.05015C14.2161 4.31648 9.78392 4.31648 7.05025 7.05015C6.65973 7.44067 6.02656 7.44067 5.63604 7.05015C5.24551 6.65962 5.24551 6.02646 5.63604 5.63593C9.15076 2.12121 14.8492 2.12121 18.364 5.63593C18.7545 6.02646 18.7545 6.65962 18.364 7.05015C17.9734 7.44067 17.3403 7.44067 16.9497 7.05015Z"
										/>
									</svg>
								{:else}
									{$t('words.submit')}
								{/if}
							</button>
						</div>
					</div>
				</form>
			</div>

			<div class="flex items-center justify-center py-4 bg-white/[0.06]">
				<a href="/account/login" class="text-sm text-ink-muted hover:text-ink hover:underline underline-offset-4">Back to sign in</a>
			</div>
		</div>
	</div>
</div>
