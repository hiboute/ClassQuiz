<!--
SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)

SPDX-License-Identifier: MPL-2.0
-->

<script lang="ts">
	import { FFmpeg } from '@ffmpeg/ffmpeg';
	import { fetchFile } from '@ffmpeg/util';
	import { navbarVisible } from '$lib/stores.svelte.ts';
	import { getLocalization } from '$lib/i18n';
	const { t } = getLocalization();

	let file_input: HTMLInputElement = $state();
	navbarVisible.visible = false;

	let stats: { progress: number; time_elapsed: number; speed: number } = $state({
		progress: 0,
		time_elapsed: 0,
		speed: 0
	});

	let upload_stats: { progress: number; upload_started: undefined | Date; time_elapsed: number } =
		$state({
			progress: 0,
			upload_started: undefined,
			time_elapsed: 0
		});

	const speed_extraction_regex = /speed=(\d+\.\d+)x(?![\s\S]*speed=\d+\.\d+x)/;
	let last_time_elapsed = 0;

	// eslint-disable-next-line no-unused-vars
	enum Status {
		// eslint-disable-next-line no-unused-vars
		Idle,
		// eslint-disable-next-line no-unused-vars
		Compressing,
		// eslint-disable-next-line no-unused-vars
		CompressDone,
		// eslint-disable-next-line no-unused-vars
		Uploading,
		// eslint-disable-next-line no-unused-vars
		Done
	}

	let status: Status = $state(Status.Idle);

	let file_size_in_mi: undefined | number = $state(undefined);
	let original_file_size_in_mi: undefined | number = undefined;
	let file_data: undefined | Blob = undefined;

	const compress_video = async () => {
		if (status !== Status.Idle) {
			return;
		}
		status = Status.Compressing;
		const ffmpeg = new FFmpeg();
		const file = file_input.files[0];
		original_file_size_in_mi = file.size / 1_048_576;
		ffmpeg.on('log', ({ message }) => {
			const speed_match = message.match(speed_extraction_regex);
			stats.speed = speed_match ? parseFloat(speed_match[1]) : 0;
		});
		ffmpeg.on('progress', (p) => {
			if (stats.progress >= 1) {
				stats.time_elapsed = last_time_elapsed;
				return;
			}
			stats.time_elapsed = p.time ?? 0;
			last_time_elapsed = stats.time_elapsed;
			stats.progress = p.ratio ?? 0;
		});
		await ffmpeg.load({
			// log: true,
		});
		await ffmpeg.writeFile(file.name, await fetchFile(file));
		await ffmpeg.exec([
			'-i',
			file.name,
			'-vcodec',
			'libx264',
			'-crf',
			'20',
			'-vf',
			'scale=1080:-2',
			'out.mp4'
		]);
		const data = await ffmpeg.readFile('out.mp4');
		file_size_in_mi = data.length / 1_048_576;
		file_data = new Blob([data]);
		status = Status.CompressDone;
		stats.progress = 1;
	};

	const upload_video = async () => {
		status = Status.Uploading;
		upload_stats.upload_started = new Date();
		/*        const progressTrackingStream = new TransformStream({
            transform(chunk, controller) {
                controller.enqueue(chunk);
                bytesUploaded += chunk.byteLength;
                console.log("upload progress:", bytesUploaded / totalBytes);
                upload_stats.progress = bytesUploaded / totalBytes;
                upload_stats.time_elapsed = (new Date() - upload_stats.upload_started) / 1000;
            },
            flush(_controller) {
                console.log("completed stream");
            }
        });*/
		/*        const response = await fetch("/api/v1/storage/raw", {
                    method: "POST",
                    headers: {
                        "Content-Type": "video/mp4"
                    },
                    body: file_data.stream().pipeThrough(progressTrackingStream),
                    duplex: "half"
                });
                const json = await response.json()*/
		const xhr = new XMLHttpRequest();
		const success = await new Promise((resolve) => {
			xhr.upload.addEventListener('progress', (event) => {
				if (event.lengthComputable) {
					upload_stats.progress = event.loaded / event.total;
					upload_stats.time_elapsed = (new Date() - upload_stats.upload_started) / 1000;
				}
			});
			xhr.addEventListener('loadend', () => {
				resolve({
					success: xhr.readyState === 4 && xhr.status === 200,
					body: xhr.responseText
				});
			});
			xhr.open('POST', '/api/v1/storage/raw', true);
			xhr.setRequestHeader('Content-Type', 'video/mp4');
			xhr.send(file_data);
		});
		console.log('success:', success);
		const json = JSON.parse(success.body);
		localStorage.setItem('video_upload_id', json.id);
		console.log(json, 'done');
		status = Status.Done;
		window.close();
	};
</script>

<div class="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-5 p-6">
	<div>
		<span class="bt-eyebrow text-[11px] text-ink-muted">Media</span>
		<h1 class="bt-headline mt-1 text-3xl">{$t('uploader.upload_a_video')}</h1>
		<p class="mt-2 text-sm text-ink-muted">
			Pick an MP4, compress it here, then upload it. This window closes when it is done.
		</p>
	</div>
	<label class="bt-glass bt-glass-faint flex cursor-pointer flex-col gap-2 p-5">
		<span class="bt-eyebrow text-[10px] text-ink-muted">1. Video file</span>
		<input type="file" bind:this={file_input} class="file" accept="video/mp4" />
	</label>
	<button
		type="button"
		class="bt-btn-ghost bt-btn-block"
		onclick={compress_video}
		disabled={status !== Status.Idle}>2. {$t('words.submit')}</button
	>
	{#if status === Status.Compressing || status === Status.CompressDone || status === Status.Uploading}
		<div class="bt-glass bt-glass-faint p-5">
			<div class="bar" aria-hidden="true">
				<span
					style="width:{Math.round(
						(status === Status.Uploading ? upload_stats.progress : stats.progress) * 100
					)}%"
				></span>
			</div>
			<dl class="mt-4 grid grid-cols-3 gap-3 text-sm">
				<div>
					<dt class="text-ink-muted">{$t('words.progress')}</dt>
					<dd class="bt-num text-2xl">
						{Math.round(
							(status === Status.Uploading ? upload_stats.progress : stats.progress) * 100
						)}%
					</dd>
				</div>
				{#if status !== Status.Uploading}
					<div>
						<dt class="text-ink-muted">{$t('words.speed')}</dt>
						<dd class="bt-num text-2xl">{stats.speed}x</dd>
					</div>
				{/if}
				<div>
					<dt class="text-ink-muted">{$t('video_uploader.time_elapsed')}</dt>
					<dd class="bt-num text-2xl">
						{(status === Status.Uploading
							? upload_stats.time_elapsed
							: stats.time_elapsed
						).toFixed(1)}s
					</dd>
				</div>
			</dl>
		</div>
	{/if}
	<button
		type="button"
		class="bt-btn-primary bt-btn-block"
		disabled={status !== Status.CompressDone}
		onclick={upload_video}
	>
		3. {$t('words.upload')}
		{file_size_in_mi ? `(${file_size_in_mi.toFixed(2)} MB)` : ''}
	</button>
</div>

<style>
	.file {
		color: var(--ink-muted);
		font-size: 14px;
	}
	.file::file-selector-button {
		margin-right: 12px;
		padding: 8px 16px;
		border: 0;
		border-radius: 999px;
		background: var(--fill-glass-strong);
		color: var(--ink);
		font-family: var(--bt-font);
		font-weight: 700;
		cursor: pointer;
	}
	.bar {
		height: 8px;
		border-radius: 999px;
		background: var(--fill-glass-mid);
		overflow: hidden;
	}
	.bar span {
		display: block;
		height: 100%;
		background: linear-gradient(90deg, var(--accent-sky), var(--accent-green));
		transition: width 200ms ease;
	}
</style>
