// SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import type { Socket } from 'socket.io-client';

/**
 * Class that encapsulates all the socket calls related to game controls for the admin page.
 * Still in development, but it will be used to avoid having socket calls directly in the svelte files, and to have a single place to manage all the game controls related socket calls.
 */
export class SocketGameControls {
	socket: Socket;

	constructor(socket: Socket) {
		this.socket = socket;
	}

	set_question_number(q_number: number) {
		this.socket.emit('set_question_number', q_number.toString());
	}

	get_question_results(game_id: string, question_number: number) {
		this.socket.emit('get_question_results', {
			game_id,
			question_number
		});
	}

	show_solutions() {
		this.socket.emit('show_solutions', {});
	}

	get_final_results() {
		this.socket.emit('get_final_results', {});
	}

	/** get_ready_seconds: length of the "get ready" screen, 0 turns it off */
	start_game(get_ready_seconds?: number) {
		this.socket.emit(
			'start_game',
			get_ready_seconds === undefined ? '' : { get_ready_seconds }
		);
	}

	kick_player<T extends { username: string }>(username: string, players: T[]): T[] {
		this.socket.emit('kick_player', { username: username });
		return players.filter((p) => p.username !== username);
	}

	lock_game() {
		this.socket.emit('lock_game', {});
	}

	unlock_game() {
		this.socket.emit('unlock_game', {});
	}

	pause_game() {
		this.socket.emit('pause_game', {});
	}

	resume_game() {
		this.socket.emit('resume_game', {});
	}

	end_game_now() {
		this.socket.emit('end_game_now', {});
	}
}
