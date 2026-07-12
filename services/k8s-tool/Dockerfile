FROM golang:1.22 AS build

WORKDIR /src

COPY services/k8s-tool/go.mod services/k8s-tool/go.sum ./
RUN go mod download

COPY services/k8s-tool ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/k8s-tool ./cmd/k8s-tool

FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=build /out/k8s-tool /k8s-tool

EXPOSE 8081

ENTRYPOINT ["/k8s-tool"]
