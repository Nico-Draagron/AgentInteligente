# Dockerfile para o projeto React/Vite
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* bun.lockb* ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
