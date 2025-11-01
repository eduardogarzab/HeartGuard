# syntax=docker/dockerfile:1

FROM golang:1.22-alpine3.20 AS build
WORKDIR /src
# Usar mirror directo de Alpine (sin CDN)
RUN echo "http://alpine.mirror.wearetriple.com/v3.20/main" > /etc/apk/repositories && \
    echo "http://alpine.mirror.wearetriple.com/v3.20/community" >> /etc/apk/repositories && \
    apk add --no-cache build-base git
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o /tmp/superadmin-api ./cmd/superadmin-api

FROM alpine:3.20
RUN echo "http://alpine.mirror.wearetriple.com/v3.20/main" > /etc/apk/repositories && \
    echo "http://alpine.mirror.wearetriple.com/v3.20/community" >> /etc/apk/repositories && \
    apk add --no-cache ca-certificates tzdata
RUN addgroup -S heartguard && adduser -S heartguard -G heartguard
WORKDIR /srv/app
COPY --from=build /tmp/superadmin-api /usr/local/bin/superadmin-api
COPY --from=build /src/templates ./templates
COPY --from=build /src/ui ./ui
COPY --from=build /src/web ./web
EXPOSE 8080
ENV HTTP_ADDR=:8080
ENV ENV=prod
USER heartguard
ENTRYPOINT ["superadmin-api"]
