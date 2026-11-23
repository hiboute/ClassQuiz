// SPDX-FileCopyrightText: 2026 Charles-Henri ROBICHE
//
// SPDX-License-Identifier: MPL-2.0

/**
 * Host screen sounds: simple tones made on the fly with WebAudio (no audio
 * files). Muted state is remembered in this browser.
 */

const KEY = 'host_sound_muted';

function readMuted(): boolean {
	try {
		return localStorage.getItem(KEY) === '1';
	} catch {
		return false;
	}
}

class HostSound {
	muted = $state(false);
	private ctx: AudioContext | null = null;

	constructor() {
		if (typeof window !== 'undefined') this.muted = readMuted();
	}

	toggle() {
		this.muted = !this.muted;
		try {
			localStorage.setItem(KEY, this.muted ? '1' : '0');
		} catch {
			/* private mode: keep it for this page only */
		}
		if (!this.muted) this.blip();
	}

	private audio(): AudioContext | null {
		if (this.muted || typeof window === 'undefined') return null;
		try {
			if (!this.ctx) {
				const Ctor =
					window.AudioContext ??
					(window as unknown as { webkitAudioContext: typeof AudioContext })
						.webkitAudioContext;
				this.ctx = new Ctor();
			}
			if (this.ctx.state === 'suspended') void this.ctx.resume();
			return this.ctx;
		} catch {
			return null;
		}
	}

	/** one note: frequency in Hz, start offset and length in seconds */
	private note(freq: number, at = 0, len = 0.18, type: OscillatorType = 'sine', vol = 0.12) {
		const ctx = this.audio();
		if (!ctx) return;
		const t = ctx.currentTime + at;
		const osc = ctx.createOscillator();
		const gain = ctx.createGain();
		osc.type = type;
		osc.frequency.setValueAtTime(freq, t);
		gain.gain.setValueAtTime(0.0001, t);
		gain.gain.exponentialRampToValueAtTime(vol, t + 0.012);
		gain.gain.exponentialRampToValueAtTime(0.0001, t + len);
		osc.connect(gain).connect(ctx.destination);
		osc.start(t);
		osc.stop(t + len + 0.05);
	}

	/** a player joined */
	blip() {
		this.note(880, 0, 0.09, 'sine', 0.06);
		this.note(1320, 0.05, 0.1, 'sine', 0.04);
	}
	/** last seconds of a countdown */
	tick(last = false) {
		this.note(last ? 660 : 520, 0, 0.08, 'triangle', 0.09);
	}
	/** get ready 3-2-1 */
	count(go = false) {
		if (go) {
			this.note(784, 0, 0.25, 'triangle', 0.12);
			this.note(1175, 0.02, 0.3, 'sine', 0.06);
		} else {
			this.note(392, 0, 0.14, 'triangle', 0.1);
		}
	}
	/** time is up */
	timeUp() {
		this.note(330, 0, 0.35, 'triangle', 0.12);
		this.note(247, 0.12, 0.45, 'triangle', 0.1);
	}
	/** answers revealed */
	reveal() {
		[523, 659, 784].forEach((f, i) => this.note(f, i * 0.07, 0.4, 'sine', 0.08));
	}
	/** podium step (rank 3, 2, 1) */
	podium(rank: number) {
		const base = rank === 1 ? 523 : rank === 2 ? 440 : 392;
		this.note(base, 0, 0.3, 'triangle', 0.1);
		this.note(base * 1.5, 0.08, 0.35, 'sine', 0.06);
		if (rank === 1) {
			[659, 784, 1047].forEach((f, i) => this.note(f, 0.25 + i * 0.12, 0.5, 'sine', 0.08));
		}
	}
}

export const hostSound = new HostSound();
