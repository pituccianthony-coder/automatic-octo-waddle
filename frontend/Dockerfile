# frontend/Dockerfile

# --- Сборка ---
# Используем образ Node.js для сборки нашего Next.js приложения.
FROM node:20-alpine AS builder
WORKDIR /app

# Копируем package.json и устанавливаем зависимости.
# Это кэшируется, чтобы не переустанавливать все каждый раз.
COPY package*.json ./
RUN npm install

# Копируем остальной код.
COPY . .

# Собираем production-ready билд.
RUN npm run build

# --- Production ---
# Теперь создаем финальный, легковесный образ.
FROM node:20-alpine
WORKDIR /app

# Копируем .next, public и package.json из сборщика.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Указываем порт, который будет слушать Next.js.
EXPOSE 3000

# Команда для запуска production-сервера.
CMD ["npm", "start"]
