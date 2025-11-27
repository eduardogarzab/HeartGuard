# syntax=docker/dockerfile:1.6
FROM golang:1.22-alpine AS builder
WORKDIR /src

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/superadmin ./cmd/superadmin-api

FROM alpine:3.20 AS runtime
WORKDIR /app

RUN apk add --no-cache ca-certificates tzdata curl

COPY --from=builder /out/superadmin /app/superadmin
COPY templates/ /app/templates/
COPY ui/ /app/ui/
COPY web/ /app/web/

ENV ENV=prod \
    HTTP_ADDR=:8080 \
    ACCESS_TOKEN_TTL=15m \
    REFRESH_TOKEN_TTL=720h \
    RATE_LIMIT_RPS=10 \
    RATE_LIMIT_BURST=20 \
    SECURE_COOKIES=true

EXPOSE 8080

CMD ["/app/superadmin"]
