FROM node:24-bookworm-slim AS build

WORKDIR /app

COPY packages ./packages
COPY apps/web/package*.json ./apps/web/
COPY apps/web/svelte.config.js ./apps/web/svelte.config.js

WORKDIR /app/apps/web
RUN npm ci --legacy-peer-deps

WORKDIR /app
COPY apps/web ./apps/web

ARG PUBLIC_API_BASE_URL=/api
ARG PUBLIC_STREAMLIT_BASE_URL=/streamlit
ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}
ENV PUBLIC_STREAMLIT_BASE_URL=${PUBLIC_STREAMLIT_BASE_URL}

WORKDIR /app/apps/web
RUN npm run build

FROM node:24-bookworm-slim AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PUBLIC_API_BASE_URL=/api
ENV PUBLIC_STREAMLIT_BASE_URL=/streamlit

COPY --from=build /app/apps/web/build ./build
COPY --from=build /app/apps/web/package.json ./package.json
COPY --from=build /app/apps/web/node_modules ./node_modules

EXPOSE 3000

CMD ["node", "build"]
