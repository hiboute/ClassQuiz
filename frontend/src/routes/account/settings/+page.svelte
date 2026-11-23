<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { getLocalization } from '$lib/i18n';
	import { DateTime } from 'luxon';
	import { UAParser } from 'ua-parser-js';
	import { onMount } from 'svelte';
	import PageHeader from '$lib/components/organiser/PageHeader.svelte';

	const { t } = getLocalization();

	interface UserAccount {
		id: string;
		email: string;
		username: string;
		verified: boolean;
		created_at: string;
	}

	interface ChangePasswordData {
		oldPassword: string;
		newPassword: string;
		newPasswordConfirm: string;
	}

	let changePasswordData: ChangePasswordData = $state({
		oldPassword: '',
		newPassword: '',
		newPasswordConfirm: ''
	});

	let password_message = $state('');
	let this_session: any = $state();

	let passwordChangeDataValid = $derived(
		changePasswordData.newPassword === changePasswordData.newPasswordConfirm &&
			changePasswordData.newPassword.length >= 8 &&
			changePasswordData.oldPassword !== changePasswordData.newPassword &&
			changePasswordData.oldPassword !== ''
	);

	const changePassword = async (e: Event) => {
		e.preventDefault();
		if (!passwordChangeDataValid) {
			return;
		}
		const res = await fetch('/api/v1/users/password/update', {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				old_password: changePasswordData.oldPassword,
				new_password: changePasswordData.newPassword
			})
		});
		if (res.status === 200) {
			password_message = 'Password changed. Sign in again with the new one.';
			setTimeout(() => window.location.assign('/account/login'), 1500);
		} else {
			password_message = 'The password could not be changed. Check the current password.';
		}
	};

	const getUser = async (): Promise<UserAccount> => {
		const response = await fetch('/api/v1/users/me', {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		});
		if (response.status === 200) {
			return await response.json();
		} else {
			window.location.assign('/account/login');
		}
	};

	onMount(() => {
		api_keys = get_api_keys();
	});

	const get_api_keys = async (): Promise<any[]> => {
		const res = await fetch('/api/v1/users/api_keys');
		const api_keys_temp = await res.json();
		return api_keys_temp;
	};

	let api_keys: Promise<any[]> | undefined = $state();

	const add_api_key = async () => {
		await fetch('/api/v1/users/api_keys', { method: 'POST' });
		api_keys = get_api_keys();
	};
	const formatDate = (date: string): string => {
		const dt = DateTime.fromISO(date);
		return dt.toLocaleString(DateTime.DATETIME_MED);
	};

	const delete_api_key = async (key: string) => {
		if (confirm('Do you really want to delete this API-Key?')) {
			await fetch(`/api/v1/users/api_keys?api_key=${key}`, { method: 'DELETE' });
			api_keys = get_api_keys();
		}
	};

	const getSessions = async () => {
		const res = await fetch('/api/v1/users/sessions/list');
		if (res.status === 200) {
			const res2 = await fetch('/api/v1/users/session');
			if (res2.status === 200) {
				this_session = await res2.json();
			}
			return await res.json();
		} else {
			window.location.assign('/account/login?returnTo=/account/settings');
		}
		return await res.json();
	};

	const getFormattedUserAgent = (userAgent: string): string => {
		const parser = new UAParser(userAgent);
		const result = parser.getResult();
		return `${result.browser.name} ${result.browser.version} (${result.os.name})`;
	};

	const deleteSession = async (session_id: string) => {
		const res = await fetch(`/api/v1/users/sessions/${session_id}`, {
			method: 'DELETE'
		});
		if (res.status === 200) {
			window.location.reload();
		}
	};
</script>

<svelte:head>
	<title>Settings - India Tech Hub Live Quiz</title>
</svelte:head>

<main class="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-10 pt-8 lg:pt-14 pb-16">
	{#await getUser()}
		<div class="h-40 flex items-center justify-center text-ink-muted">Loading</div>
	{:then user}
		<PageHeader eyebrow="Account" kicker={user.email} headline={user.username}>
			{#snippet actions()}
				<a href="/dashboard" class="bt-btn-ghost">Dashboard</a>
			{/snippet}
		</PageHeader>

		<div class="mt-10 grid gap-4 lg:grid-cols-[280px_1fr]">
			<section class="bt-glass bt-glass-faint p-6 flex flex-col items-center gap-5" aria-label="Avatar">
				<img
					class="h-40 w-40 rounded-full bg-white/10 object-cover"
					src="/api/v1/users/avatar"
					alt=""
				/>
				<a href="/account/settings/avatar" class="bt-btn-ghost bt-btn-block !text-sm"
					>{$t('settings_page.change_avatar')}</a
				>
				<div class="w-full flex flex-col gap-1 text-sm">
					<a
						href="/account/settings/security"
						class="rounded-[12px] px-3 py-2 hover:bg-white/10 flex justify-between"
						>{$t('settings_page.security_settings')}<span aria-hidden="true">&rsaquo;</span></a
					>
					<a
						href="/user/{user.id}"
						class="rounded-[12px] px-3 py-2 hover:bg-white/10 flex justify-between"
						>Public profile page<span aria-hidden="true">&rsaquo;</span></a
					>
				</div>
			</section>

			<section class="bt-glass bt-glass-faint p-6 sm:p-8">
				<span class="bt-eyebrow text-ink-muted mb-2">Password</span>
				<h2 class="font-black text-2xl uppercase">{$t('settings_page.change_password_submit')}</h2>
				<form class="mt-6 grid gap-4 sm:grid-cols-3" onsubmit={changePassword}>
					<label class="flex flex-col gap-2">
						<span class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
							>{$t('settings_page.old_password')}</span
						>
						<input
							type="password"
							class="bt-input !text-base"
							autocomplete="current-password"
							bind:value={changePasswordData.oldPassword}
						/>
					</label>
					<label class="flex flex-col gap-2">
						<span class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
							>{$t('settings_page.new_password')}</span
						>
						<input
							type="password"
							class="bt-input !text-base"
							autocomplete="new-password"
							bind:value={changePasswordData.newPassword}
						/>
					</label>
					<label class="flex flex-col gap-2">
						<span class="bt-eyebrow !text-[11px] !tracking-[3px] text-ink-muted"
							>{$t('settings_page.repeat_password')}</span
						>
						<input
							type="password"
							class="bt-input !text-base"
							autocomplete="new-password"
							bind:value={changePasswordData.newPasswordConfirm}
						/>
					</label>
					<div class="sm:col-span-3 flex flex-wrap items-center gap-4">
						<button class="bt-btn-primary" disabled={!passwordChangeDataValid} type="submit">
							{$t('settings_page.change_password_submit')}
						</button>
						<p class="text-sm text-ink-muted" role="status">
							{password_message || 'At least 8 characters, different from the current one.'}
						</p>
					</div>
				</form>
			</section>
		</div>

		<section class="bt-glass bt-glass-faint mt-4 p-6 sm:p-8">
			<div class="flex flex-wrap items-end justify-between gap-4">
				<div>
					<span class="bt-eyebrow text-ink-muted mb-2">Integrations</span>
					<h2 class="font-black text-2xl uppercase">API keys</h2>
				</div>
				<button type="button" class="bt-btn-ghost !text-sm" onclick={add_api_key}
					>{$t('settings_page.add_api_key')}</button
				>
			</div>
			{#await api_keys}
				<p class="mt-4 text-ink-muted">Loading</p>
			{:then keys}
				{#if keys?.length}
					<ul class="mt-5 flex flex-col gap-2">
						{#each keys as key}
							<li class="flex items-center gap-3 rounded-[12px] bg-white/[0.06] ps-4 pe-2 py-2">
								<code class="flex-1 min-w-0 truncate text-sm">{key.key}</code>
								<button
									type="button"
									class="rounded-full px-4 py-2 text-sm hover:bg-white/10 text-[#ff9db0]"
									onclick={() => delete_api_key(key.key)}>{$t('words.delete')}</button
								>
							</li>
						{/each}
					</ul>
				{:else}
					<p class="mt-4 text-sm text-ink-muted">No API key yet.</p>
				{/if}
			{/await}
		</section>
	{/await}

	{#await getSessions() then sessions}
		<section class="bt-glass bt-glass-faint mt-4 p-6 sm:p-8">
			<span class="bt-eyebrow text-ink-muted mb-2">Security</span>
			<h2 class="font-black text-2xl uppercase">Signed-in sessions</h2>
			<div class="mt-5 overflow-x-auto -mx-2">
				<table class="min-w-full text-sm">
					<thead>
						<tr class="text-start text-ink-muted">
							<th scope="col" class="px-2 py-2 font-normal text-start uppercase text-[11px] tracking-[2px]"
								>{$t('words.browser')}</th
							>
							<th scope="col" class="px-2 py-2 font-normal text-start uppercase text-[11px] tracking-[2px]"
								>{$t('overview_page.created_at')}</th
							>
							<th scope="col" class="px-2 py-2 font-normal text-start uppercase text-[11px] tracking-[2px]"
								>{$t('settings_page.last_seen')}</th
							>
							<th scope="col" class="px-2 py-2"><span class="sr-only">Actions</span></th>
						</tr>
					</thead>
					<tbody>
						{#each sessions as session}
							<tr class="border-t border-white/10">
								<td class="px-2 py-3 whitespace-nowrap">
									{getFormattedUserAgent(session.user_agent)}
									{#if session.id === this_session?.id}
										<span
											class="ms-2 rounded-full bg-[var(--accent-green)]/25 px-2 py-0.5 text-[11px] uppercase tracking-[2px]"
											>This device</span
										>
									{/if}
								</td>
								<td class="px-2 py-3 whitespace-nowrap text-ink-muted">{formatDate(session.created_at)}</td>
								<td class="px-2 py-3 whitespace-nowrap text-ink-muted">{formatDate(session.last_seen)}</td>
								<td class="px-2 py-3 text-end">
									<button
										type="button"
										class="rounded-full px-4 py-1.5 hover:bg-white/10 text-[#ff9db0]"
										onclick={() => deleteSession(session.id)}>Sign out</button
									>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>
	{/await}
</main>
