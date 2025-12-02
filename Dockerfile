ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION} AS buildenv
ARG POETRY_VERSION=1.8.2
RUN pip install poetry==${POETRY_VERSION}

WORKDIR /app

# Cache main dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --only main --no-root

COPY ./ ./
RUN . .venv/bin/activate \
    && pip install --no-deps .

FROM python:${PYTHON_VERSION}-slim AS dlm_runtime

RUN apt-get update && apt-get install -y rclone openssh-server && \
    ssh-keygen -A && \
    openssl req -x509 -nodes -days 365 \
        -subj "/C=AU/ST=WA/O=SKAO, Inc./CN=skao.int" \
        -addext "subjectAltName=DNS:skao.int" \
        -newkey rsa:2048 \
        -keyout /etc/ssl/private/selfsigned.key \
        -out /etc/ssl/certs/selfsigned.cert

# Best practice not to run as root
RUN useradd ska-dlm
RUN mkdir -p /home/ska-dlm/.ssh
RUN chown -R ska-dlm /home/ska-dlm
USER ska-dlm

# Copy all Python packages & console scripts to the runtime container
COPY --from=buildenv /app/.venv /app/.venv/
COPY tests/entrypoint.sh /entrypoint.sh
ENV PATH="/app/.venv/bin:${PATH}"
USER root
ENTRYPOINT [ "/entrypoint.sh" ]
