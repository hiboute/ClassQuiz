<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->
<script lang="ts">
	let { session_data = {}, step, selected_method = $bindable() } = $props();

	const METHODS = [
		{
			id: 'PASSKEY',
			title: 'Security key',
			hint: 'Use a passkey or a hardware key',
			// heroicons/key
			icon: 'M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z'
		},
		{
			id: 'PASSWORD',
			title: 'Password',
			hint: 'Type your account password',
			// heroicons/lock-closed
			icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z'
		},
		{
			id: 'TOTP',
			title: 'Authenticator code',
			hint: 'Six digits from your authenticator app',
			// heroicons/clock
			icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
		}
	];

	let available_methods: string[] = $derived(
		(step === 1 ? session_data.step_1 : step === 2 ? session_data.step_2 : []) ?? []
	);
</script>

<div class="p-6 sm:p-8">
	<span class="bt-eyebrow text-ink-muted mb-3">Sign in</span>
	<h2 class="bt-headline text-[28px] sm:text-[34px]">
		{step === 2 ? 'One more step' : 'Choose a method'}
	</h2>

	<ul class="mt-6 flex flex-col gap-3">
		{#each METHODS.filter((m) => available_methods.includes(m.id)) as m}
			<li>
				<button
					type="button"
					class="w-full flex items-center gap-4 rounded-[18px] bg-white/[0.08] hover:bg-white/[0.14] transition-colors p-4 text-start"
					onclick={() => (selected_method = m.id)}
				>
					<span class="h-12 w-12 shrink-0 rounded-[12px] bg-[var(--fill-deep)] flex items-center justify-center">
						<svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"
							><path stroke-linecap="round" stroke-linejoin="round" d={m.icon} /></svg
						>
					</span>
					<span>
						<span class="block font-bold">{m.title}</span>
						<span class="block text-sm text-ink-muted">{m.hint}</span>
					</span>
				</button>
			</li>
		{/each}
	</ul>
</div>
