FROM postgres:latest

# set authentication to scram-sha-256
COPY postgresql.conf /etc/postgresql/postgresql.conf

WORKDIR /app

COPY add_user .
RUN chmod +x add_user

