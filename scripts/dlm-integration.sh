#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

export DLM_SERVER_DIR="$root/build/dlm-server"
server_repository=${DLM_SERVER_REPOSITORY:-https://gitlab.com/ska-telescope/ska-data-lifecycle.git}
project=dlm-client-integration
compose=(docker compose --project-name "$project"
    --file tests/dlm_clients.docker-compose.yaml
    --file tests/integration-compose.override.yaml)

fail() {
    echo "DLM integration: $*" >&2
    exit 1
}

configure_compose() {
    local services service volumes
    [[ -f $DLM_SERVER_DIR/tests/dlm.docker-compose.yaml ]] \
        || fail "server checkout does not provide tests/dlm.docker-compose.yaml"
    services=$(docker compose --file "$DLM_SERVER_DIR/tests/dlm.docker-compose.yaml" config --services) \
        || fail "cannot read the server Compose configuration"
    volumes=$(docker compose --file "$DLM_SERVER_DIR/tests/dlm.docker-compose.yaml" config --volumes) \
        || fail "cannot read the server Compose volumes"
    if grep -Fxq data <<< "$volumes"; then
        export DLM_DATA_VOLUME=data
    elif grep -Fxq shared-tmpfs <<< "$volumes"; then
        export DLM_DATA_VOLUME=shared-tmpfs
    else
        fail "server revision has no supported data volume"
    fi
    for service in dlm_storage dlm_ingest dlm_request dlm_migration dlm_outbox dlm_heuristics; do
        grep -Fxq "$service" <<< "$services" \
            || fail "server revision lacks required service $service and is incompatible"
    done
    if grep -Fxq dlm_rclone_worker <<< "$services" \
        && grep -Fxq rclone-key-init <<< "$services"; then
        compose+=(--file tests/integration-compose.embedded.yaml)
    elif grep -Fxq dlm_rclone <<< "$services"; then
        compose+=(--file tests/integration-compose.rclone.yaml)
    else
        fail "server revision has no supported rclone service"
    fi
}

check_owned_resources() {
    local kind name owner resource
    for resource in network:dlm-client-integration-network \
        volume:dlm-client-integration-data volume:dlm-client-integration-server-data \
        volume:dlm-client-integration_rclone-ssh-keys; do
        kind=${resource%%:*}
        name=${resource#*:}
        if docker "$kind" inspect "$name" >/dev/null 2>&1; then
            owner=$(docker "$kind" inspect "$name" \
                --format '{{ index .Labels "com.docker.compose.project" }}')
            [[ $owner == "$project" ]] || fail "$kind $name already exists and is not owned by $project"
        fi
    done
}

prepare_server() {
    local ref commit
    ref=${DLM_SERVER_REF:-}
    [[ -n $ref ]] || fail "set DLM_SERVER_REF to a server Git tag or commit"
    [[ $ref != -* ]] || fail "invalid server ref: $ref"
    if [[ -n $(docker ps -aq --filter "label=com.docker.compose.project=$project") ]]; then
        fail "the $project stack already exists; run make docker-compose-down first"
    fi
    check_owned_resources

    if [[ ! -e $DLM_SERVER_DIR ]]; then
        mkdir -p "$(dirname "$DLM_SERVER_DIR")"
        git clone --no-recurse-submodules "$server_repository" "$DLM_SERVER_DIR"
    fi
    [[ -d $DLM_SERVER_DIR/.git ]] || fail "$DLM_SERVER_DIR is not a Git checkout"
    [[ $(git -C "$DLM_SERVER_DIR" remote get-url origin) == "$server_repository" ]] \
        || fail "$DLM_SERVER_DIR has a different origin; choose a fresh checkout location"
    [[ -z $(git -C "$DLM_SERVER_DIR" status --porcelain --untracked-files=normal) ]] \
        || fail "$DLM_SERVER_DIR has local changes; preserve or remove them before continuing"
    git -C "$DLM_SERVER_DIR" fetch --prune --tags origin

    if git -C "$DLM_SERVER_DIR" rev-parse --verify --quiet "refs/tags/$ref^{commit}" >/dev/null; then
        commit=$(git -C "$DLM_SERVER_DIR" rev-parse "refs/tags/$ref^{commit}")
    elif [[ $ref =~ ^[[:xdigit:]]{7,40}$ ]]; then
        if ! git -C "$DLM_SERVER_DIR" cat-file -e "$ref^{commit}" 2>/dev/null; then
            git -C "$DLM_SERVER_DIR" fetch origin "$ref" \
                || fail "cannot fetch server commit $ref"
        fi
        commit=$(git -C "$DLM_SERVER_DIR" rev-parse --verify "$ref^{commit}") \
            || fail "cannot resolve server commit $ref"
    else
        fail "server ref '$ref' is not an available tag or commit"
    fi
    git -C "$DLM_SERVER_DIR" checkout --detach "$commit"
    echo "Using DLM server $ref ($commit)"
    configure_compose
    "${compose[@]}" config --quiet \
        || fail "server revision $commit is incompatible with the client integration stack"
}

down() {
    [[ -d $DLM_SERVER_DIR/.git ]] || fail "no server checkout exists at $DLM_SERVER_DIR"
    check_owned_resources
    "${compose[@]}" down --volumes --remove-orphans
}

run_tests() {
    local ref=${DLM_SERVER_REF:-} commit running fixture pb
    running=$(docker ps -q --filter "label=com.docker.compose.project=$project" \
        --filter "label=com.docker.compose.service=dlm_storage" --filter status=running)
    [[ -n $running ]] || fail "the server stack is not running; use make docker-compose-up DLM_SERVER_REF=<tag-or-commit>"
    if [[ -n $ref ]]; then
        if git -C "$DLM_SERVER_DIR" rev-parse --verify --quiet "refs/tags/$ref^{commit}" >/dev/null; then
            commit=$(git -C "$DLM_SERVER_DIR" rev-parse "refs/tags/$ref^{commit}")
        elif [[ $ref =~ ^[[:xdigit:]]{7,40}$ ]]; then
            commit=$(git -C "$DLM_SERVER_DIR" rev-parse --verify --quiet "$ref^{commit}") \
                || fail "cannot resolve server commit $ref in the running checkout"
        else
            fail "server ref '$ref' is not an available tag or commit"
        fi
        [[ $commit == "$(git -C "$DLM_SERVER_DIR" rev-parse HEAD)" ]] \
            || fail "server ref $ref does not match the running checkout; restart the stack first"
    fi
    for pb in pb-test-20260126-24294 pb-test-20260126-24295; do
        fixture="/dlm/product_dir/product/eb-00000000/ska-sdp/$pb/scan90-99/output.scan-99.beam-vis0.ms/table.dat"
        docker exec dlm-client-integration-dlm_configdb_watcher test -f "$fixture" \
            || fail "integration fixture missing from the watcher: $fixture; run make extract-test-data and restart the stack before testing"
    done
    case $1 in
        integration) "${compose[@]}" run --rm --no-deps --entrypoint "pytest -m integration" dlm_client_testrunner ;;
        all) "${compose[@]}" run --rm --no-deps dlm_client_testrunner ;;
    esac
}

cleanup() {
    local status=$? cleanup_status=0 containers container
    trap - EXIT
    if (( status != 0 )); then
        "${compose[@]}" ps -a || true
        if containers=$("${compose[@]}" ps --all -q); then
            while IFS= read -r container; do
                [[ -n $container ]] || continue
                docker inspect --format \
                    '{{if .State.Health}}{{if ne .State.Health.Status "healthy"}}{{.Name}}: {{json .State.Health}}{{end}}{{end}}' \
                    "$container" || echo "DLM integration: cannot inspect container $container" >&2
            done <<< "$containers"
        else
            echo "DLM integration: cannot list containers for health diagnostics" >&2
        fi
        "${compose[@]}" logs --no-color --tail 200 || true
    fi
    down || cleanup_status=$?
    if [[ ${clean_test_data:-0} == 1 ]]; then
        make test-cleanup || cleanup_status=$?
    fi
    if (( status == 0 )); then
        status=$cleanup_status
    fi
    exit "$status"
}

case ${1:-} in
    test|all-tests|test-keep)
        prepare_server
        make test-cleanup extract-test-data
        clean_test_data=1
        if [[ $1 != test-keep ]]; then
            trap cleanup EXIT
        fi
        "${compose[@]}" up --build --detach --wait --wait-timeout 300 \
            --scale dlm_client_testrunner=0
        if [[ $1 == all-tests ]]; then
            run_tests all
        else
            run_tests integration
        fi
        ;;
    up)
        prepare_server
        make extract-test-data
        trap cleanup EXIT
        "${compose[@]}" up --build --detach --wait --wait-timeout 300 \
            --scale dlm_client_testrunner=0
        trap - EXIT
        ;;
    down)
        configure_compose
        down
        ;;
    run-integration-test)
        configure_compose
        run_tests integration
        ;;
    run-all-tests)
        configure_compose
        run_tests all
        ;;
    openapi)
        prepare_server
        trap cleanup EXIT
        "${compose[@]}" up --build --detach --wait --wait-timeout 300 \
            dlm_gateway dlm_ingest dlm_request dlm_storage dlm_migration
        (cd openapi_client_dlm_specs && bash generate_code.sh)
        ;;
    *)
        fail "unknown command: ${1:-<missing>}"
        ;;
esac
