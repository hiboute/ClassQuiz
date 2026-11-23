// SPDX-FileCopyrightText: 2026 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

import type { Player, PlayerAnswer } from '$lib/admin.ts';
import type { PlayGame } from '$lib/quiz_types';
import type {
	GetReadyData,
	LeaderboardData,
	PodiumData,
	ResultEntry,
	WordCount
} from '$lib/play/host/worlds';

export interface HostPlayer extends Player {
	late?: boolean;
	/** Date.now() when the host saw the join (lobby highlight) */
	joined_at?: number;
}

/** What the host screen shows after a question's results arrived. */
export type ResultsView = 'reveal' | 'leaderboard';

/**
 * Everything the host big screen needs. The admin page fills it from socket
 * events; the demo route fills it with fake data.
 */
export interface IGameState {
	game_id: string;
	players: HostPlayer[];
	player_scores: Record<string, number>;
	selected_question: number;
	timer_res: string;
	question_results: ResultEntry[] | null | undefined;
	answer_count: number;
	/** players in the game, from player_answer (falls back to players.length) */
	player_count: number;
	shown_question_now: number;
	final_results: Array<null> | Record<string, PlayerAnswer[]>;
	game_started: boolean;
	quiz_data: PlayGame;
	control_visible: boolean;
	locked: boolean;
	get_ready: GetReadyData | null;
	paused: boolean;
	words: WordCount[];
	leaderboard: LeaderboardData | null;
	previous_ranks: Record<string, number> | null;
	podium: PodiumData | null;
	results_view: ResultsView;
	toasts: { id: number; text: string }[];
}

export type GameState = IGameState;
