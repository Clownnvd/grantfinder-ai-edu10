FROM node:22-alpine AS deps
RUN corepack enable && corepack prepare pnpm@10.26.2 --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
RUN corepack enable && corepack prepare pnpm@10.26.2 --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_BFF_URL=http://127.0.0.1:8000
ENV NEXT_PUBLIC_BFF_URL=$NEXT_PUBLIC_BFF_URL
RUN pnpm build

FROM node:22-alpine AS runtime
RUN corepack enable && corepack prepare pnpm@10.26.2 --activate
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/package.json /app/pnpm-lock.yaml ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["pnpm", "start"]
