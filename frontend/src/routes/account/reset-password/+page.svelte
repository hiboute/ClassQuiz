<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { navbarVisible } from '$lib/stores.svelte.ts';

	navbarVisible.visible = true;

	const { t } = getLocalization();

	let isSubmitting = $state(false);

	const submit = async (e: Event) => {
		e.preventDefault();
		isSubmitting = true;
		const res = await fetch('/api/v1/users/forgot-password', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email: email
			})
		});
		if (res.status === 200) {
			alert('Email was sent! Please check your inbox.');
			return;
		} else if (res.status === 404) {
			alert('user not found!');
		}
		isSubmitting = false;
	};

	let email = $state('');
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
				<h2 class="bt-headline text-[28px] sm:text-[34px]">Reset password</h2>

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
									id="email"
									bind:value={email}
									name="email"
									type="email"
									class="bt-input"
									placeholder={$t('words.email')}
								/>
								<label
									for="email"
									class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
								>
									{$t('words.email')}
								</label>
							</div>
						</div>

						<div class="flex flex-wrap items-center justify-between gap-3 mt-6 gap-2">
							<a
								href="/account/login"
								class="text-sm text-ink-muted hover:text-ink hover:underline underline-offset-4"
								>{$t('register_page.already_have_account?')}</a
							>

							<button
								class="bt-btn-primary"
								disabled={email === ''}
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
