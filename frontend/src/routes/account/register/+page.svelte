<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { createForm } from 'felte';
	import { getLocalization } from '$lib/i18n';
	import { validateSchema } from '@felte/validator-yup';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import Footer from '$lib/footer.svelte';

	const { t } = getLocalization();
	import reporter from '@felte/reporter-tippy';

	navbarVisible.visible = true;
	import * as yup from 'yup';

	const registerSchema = yup.object({
		email: yup.string().email('Enter a valid email address.').required(),
		password1: yup
			.string()
			.required()
			.min(8, 'Use at least 8 characters.')
			.max(100, 'Use at most 100 characters.'),
		password2: yup
			.string()
			.required()
			.test('equal', 'The passwords do not match.', function (v) {
				const ref = yup.ref('password1');
				return v === this.resolve(ref);
			}),
		username: yup
			.string()
			.required()
			.min(3, 'Username must be at least 3 characters long')
			.max(20, 'Username must be at most 20 characters long'),
		privacy_accept: yup
			.boolean()
			.oneOf([true], 'Accept the privacy policy to continue.'),
		tos_accept: yup.boolean().oneOf([true], 'Accept the terms of service to continue.')
	});

	const { form, errors, touched, isValid, isSubmitting } = createForm<
		yup.InferType<typeof registerSchema>
	>({
		validate: validateSchema(registerSchema),
		extend: [reporter()],
		onSubmit: async (values) => {
			const res = await fetch('/api/v1/users/create', {
				method: 'post',
				body: JSON.stringify({
					email: values.email,
					password: values.password1,
					username: values.username
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			});
			if (res.status === 200) {
				responseData.data = '200';
			} else if (res.status === 409) {
				responseData.data = '409';
			} else if (res.status === 400) {
				responseData.data = '400';
			} else {
				responseData.data = 'error';
			}
			responseData.open = true;
		}
	});
	let responseData = $state({
		open: false,
		data: ''
	});
</script>

<svelte:head>
	<title>India Tech Hub Live Quiz - Register</title>
</svelte:head>
<div class="flex items-center justify-center min-h-[calc(100dvh-4rem)] px-4 py-10">
	<div>
		<div
			class="bt-glass w-full max-w-md mx-auto overflow-hidden"
		>
			<div class="p-6 sm:p-8">
				<span class="bt-eyebrow text-ink-muted mb-3">Organisers</span>
				<h2 class="bt-headline text-[28px] sm:text-[34px]">Create account</h2>

				<h3 class="mt-2 text-lg font-bold">
					{$t('register_page.greeting')}
				</h3>

				<p class="mt-1 text-ink-muted">
					{$t('register_page.create_account')}
				</p>

				<form use:form>
					<div class="w-full mt-4">
						<div class="pt-4">
							<div class="flex flex-col-reverse gap-2">
								<input
									id="email"
									name="email"
									type="email"
									class="bt-input"
									placeholder={$t('words.email')}
									class:ring-red-700={$errors.email !== null}
									class:ring-green-600={$touched.email === true &&
										$errors.email === null}
								/>
								<label
									for="email"
									class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
								>
									{$t('words.email')}
								</label>
							</div>
						</div>
						<div class="pt-4">
							<div class="flex flex-col-reverse gap-2">
								<input
									id="username"
									name="username"
									type="text"
									class="bt-input"
									placeholder={$t('words.username')}
									class:ring-red-700={$errors.username !== null}
									class:ring-green-600={$touched.username === true &&
										$errors.username === null}
								/>
								<label
									for="username"
									class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
								>
									{$t('words.username')}
								</label>
							</div>
						</div>
						<div class="pt-4">
							<div class="flex flex-col-reverse gap-2">
								<input
									id="password1"
									name="password1"
									type="password"
									class:ring-red-700={$errors.password1 !== null}
									class:ring-green-600={$touched.password1 === true &&
										$errors.password1 === null}
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
									class="bt-input"
									placeholder={$t('words.password')}
									class:ring-red-700={$errors.password2 !== null}
									class:ring-green-600={$touched.password2 === true &&
										$errors.password2 === null}
								/>
								<label
									for="password2"
									class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
								>
									{$t('words.password')}
								</label>
							</div>
						</div>
						<div
							class="flex items-center gap-3 rounded-[18px] bg-white/[0.06] mt-4 px-4 py-3"
							class:ring-red-700={$errors.privacy_accept !== null}
							class:ring-green-600={$touched.privacy_accept === true &&
								$errors.privacy_accept === null}
						>
							<!--						<div class='flex items-center justify-between mt-4 w-full'>-->
							<input type="checkbox" name="privacy_accept" class="h-4 w-4 accent-[var(--accent-green)]" />
							<label class="text-sm text-ink-muted">
								I've read the <a href="/docs/privacy-policy" class="underline"
									>Privacy policy</a
								>.
							</label>
						</div>
						<div
							class="flex items-center gap-3 rounded-[18px] bg-white/[0.06] mt-4 px-4 py-3"
							class:ring-red-700={$errors.tos_accept !== null}
							class:ring-green-600={$touched.tos_accept === true &&
								$errors.tos_accept === null}
						>
							<!--						<div class='flex items-center justify-between mt-4 w-full'>-->
							<input type="checkbox" name="tos_accept" class="h-4 w-4 accent-[var(--accent-green)]" />
							<label class="text-sm text-ink-muted">
								I agree to the <a href="/docs/tos" class="underline"
									>Terms of Service</a
								>.
							</label>
						</div>

						<div class="flex flex-wrap items-center justify-between gap-3 mt-6">
							<a
								href="/account/reset-password"
								class="text-sm text-ink-muted hover:text-ink hover:underline underline-offset-4"
								>{$t('register_page.forgot_password?')}</a
							>

							<button
								class="bt-btn-primary"
								disabled={!$isValid || $isSubmitting}
								class:cursor-not-allowed={!$isValid || $isSubmitting}
								class:opacity-50={!$isValid || $isSubmitting}
								type="submit"
							>
								{#if $isSubmitting}
									<svg class="h-4 w-4 animate-spin" viewBox="3 3 18 18">
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
									{$t('words.register')}
								{/if}
							</button>
						</div>
					</div>
				</form>
			</div>

			<div
				class="flex items-center justify-center py-4 bg-white/[0.06]"
			>
				<span class="text-sm text-ink-muted"
					>{$t('register_page.already_have_account?')}
				</span>

				<a
					href="/account/login"
					class="mx-2 text-sm font-bold hover:underline underline-offset-4"
					>{$t('words.login')}</a
				>
			</div>
		</div>
	</div>
</div>
<Footer />
<div
	class="fixed z-20 inset-0 overflow-y-auto"
	aria-labelledby="modal-title"
	role="dialog"
	aria-modal="true"
	class:hidden={!responseData.open}
>
	<div
		class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
	>
		<div class="fixed inset-0 bg-[#05040f]/70 transition-opacity" aria-hidden="true"></div>

		<!-- This element is to trick the browser into centering the modal contents. -->
		<span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true"
			>&#8203;</span
		>
		<div
			class="relative z-10 inline-block align-bottom bg-[#1a1440] rounded-[25px] text-start overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"
		>
			<div class="px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
				<div class="sm:flex sm:items-start">
					<div
						class="mx-auto shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10"
					>
						<!-- Heroicon name: outline/exclamation -->
						{#if responseData.data === '409' || responseData.data === 'error' || responseData.data === '400'}
							<svg
								class="h-6 w-6 text-red-600"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								aria-hidden="true"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
								/>
							</svg>
						{:else}
							<svg
								class="w-6 h-6 text-green-600"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
						{/if}
					</div>
					<div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
						<h3 class="text-lg leading-6 font-bold text-ink" id="modal-title">
							{#if responseData.data === '409'}
								Account already exists!
							{:else if responseData.data === 'error'}
								Unexpected error!
							{:else if responseData.data === '200'}
								Sign up successfully!
							{:else if responseData.data === '400'}
								Wrong email!
							{:else}
								You stupid Mawoka!
							{/if}
						</h3>
						<div class="mt-2">
							<p class="text-sm text-ink-muted">
								{#if responseData.data === '200'}
									<!-- TODO: Add translation -->
									You signed up. Please check your mailbox to confirm
									your email address!
								{:else if responseData.data === '409'}
									An account with that email-address already exists!
								{:else if responseData.data === '400'}
									This email-address doesn't exist!
								{:else if responseData.data === 'error'}
									There was the good old unexpected error!
								{:else}
									You stupid Mawoka!
								{/if}
							</p>
						</div>
					</div>
				</div>
			</div>
			<div class="bg-white/[0.06] px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
				<button
					type="button"
					onclick={() => {
						responseData.open = false;
						if (responseData.data === '200') {
							window.location.assign('/');
						} else {
							window.location.reload();
						}
					}}
					class="bt-btn-ghost mt-3 w-full sm:mt-0 sm:ms-3 sm:w-auto"
					>{$t('words.close')}
				</button>
			</div>
		</div>
	</div>
</div>
