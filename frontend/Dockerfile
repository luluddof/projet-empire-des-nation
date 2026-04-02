FROM node:20-bookworm-slim

WORKDIR /app

COPY package.json ./
# Le package-lock est généré sur Windows : il peut omettre les binaires optionnels
# nécessaires sous Linux (ex. Rollup). Dans l'image Docker, on fait une install
# "native Linux" et on n'utilise pas le lockfile.
RUN npm install --no-package-lock

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
