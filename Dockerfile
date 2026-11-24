FROM artefact.skao.int/ska-build-python-ubuntu24:1.1.5 AS buildenv

WORKDIR /app

# Cache main dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
    && poetry env use python3.12 \
    && poetry install --only main --no-root

COPY src/ src/
COPY README.md ./
RUN . .venv/bin/activate \
    && pip install --no-deps .

FROM artefact.skao.int/ska-python-ubuntu24:1.1.5 AS runtime

RUN apt-get update && apt-get install -y rclone openssh-server && \
    ssh-keygen -A && \
    openssl req -x509 -nodes -days 365 \
        -subj "/C=AU/ST=WA/O=SKAO, Inc./CN=skao.int" \
        -addext "subjectAltName=DNS:skao.int" \
        -newkey rsa:2048 \
        -keyout /etc/ssl/private/selfsigned.key \
        -out /etc/ssl/certs/selfsigned.cert

# Create the ska-dlm user with a home directory and Bash as the login shell
RUN useradd -ms /bin/bash ska-dlm
# Create the SSH directory and set ownership
RUN mkdir -p /home/ska-dlm/.ssh
RUN chown -R ska-dlm:ska-dlm /home/ska-dlm
# Run as a non-root user
USER ska-dlm

# Copy all Python packages & console scripts to the runtime container
COPY --from=buildenv /app/.venv /app/.venv/
COPY tests/entrypoint.sh /entrypoint.sh
ENV PATH="/app/.venv/bin:${PATH}"
USER root
