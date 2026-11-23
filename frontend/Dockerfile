# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
#
# SPDX-License-Identifier: MPL-2.0

### Build Step
# pull the Node.js Docker image
FROM node:24-trixie AS builder
ENV CI=true
# Build-time switches, read by Vite into the bundle (src/lib/config.ts). Any
# non-empty value counts as "on", so leave a switch empty to turn it off.
# Defaults are for quiz.indiatechhub.xyz: no captcha, no Google/GitHub login,
# no analytics, self sign-up hidden (the backend refuses it too with
# REGISTRATION_DISABLED=True).
ARG VITE_REGISTRATION_DISABLED=true
ARG VITE_CAPTCHA_ENABLED=
ARG VITE_HCAPTCHA=
ARG VITE_RECAPTCHA=
ARG VITE_GOOGLE_AUTH_ENABLED=
ARG VITE_GITHUB_AUTH_ENABLED=
ARG VITE_SENTRY=
ARG VITE_PLAUSIBLE_DATA_URL=
ENV VITE_REGISTRATION_DISABLED=$VITE_REGISTRATION_DISABLED \
    VITE_CAPTCHA_ENABLED=$VITE_CAPTCHA_ENABLED \
    VITE_HCAPTCHA=$VITE_HCAPTCHA \
    VITE_RECAPTCHA=$VITE_RECAPTCHA \
    VITE_GOOGLE_AUTH_ENABLED=$VITE_GOOGLE_AUTH_ENABLED \
    VITE_GITHUB_AUTH_ENABLED=$VITE_GITHUB_AUTH_ENABLED \
    VITE_SENTRY=$VITE_SENTRY \
    VITE_PLAUSIBLE_DATA_URL=$VITE_PLAUSIBLE_DATA_URL
# change working directory
WORKDIR /usr/src/app


# copy the package.json files from local machine to the workdir in container
COPY package*.json ./
COPY pnpm-lock.yaml ./
COPY pnpm-workspace.yaml ./

# run npm install in our local machine
RUN corepack enable && corepack prepare pnpm@11.6 --activate && pnpm ci --ignore-scripts

# copy the generated modules and all other files to the container
COPY . .

# build the application
RUN pnpm run build

### Serve Step
# pull the Node.js Docker image
FROM node:24-trixie-slim
ENV CI=true

# change working directory
WORKDIR /app
COPY --from=builder /usr/src/app/package.json .
COPY --from=builder /usr/src/app/pnpm-lock.yaml .
RUN corepack enable && corepack prepare pnpm@11.6 --activate && pnpm ci --ignore-scripts
# copy files from previous step
COPY --from=builder /usr/src/app/build .
COPY --from=builder /usr/src/app/node_modules ./node_modules

# our app is running on port 3000 within the container, so need to expose it
EXPOSE 3000

# the command that starts our app
CMD ["pnpm", "run", "run:prod"]
