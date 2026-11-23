// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

// the old prefix: import.meta.env.VITE_
export const google_auth_enabled = import.meta.env.VITE_GOOGLE_AUTH_ENABLED;
export const github_auth_enabled = import.meta.env.VITE_GITHUB_AUTH_ENABLED;
// Captcha is off unless VITE_CAPTCHA_ENABLED is exactly "true" (the string "false" is truthy).
export const captcha_enabled = import.meta.env.VITE_CAPTCHA_ENABLED === 'true';
export const custom_oauth_name = import.meta.env.VITE_CUSTOM_OAUTH_NAME;
export const registration_disabled = import.meta.env.VITE_REGISTRATION_DISABLED;
export const hcaptcha_site_key = captcha_enabled ? import.meta.env.VITE_HCAPTCHA : undefined;
export const sentry_dsn = import.meta.env.VITE_SENTRY;
export const recaptcha_key = captcha_enabled ? import.meta.env.VITE_RECAPTCHA : undefined;
export const plausible_data_url = import.meta.env.VITE_PLAUSIBLE_DATA_URL;
