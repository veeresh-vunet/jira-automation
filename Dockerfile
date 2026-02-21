FROM python:3.11-slim

WORKDIR /app

COPY dist/main .

RUN chmod +x ./main

CMD ["./main"]