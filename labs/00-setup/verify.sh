#!/usr/bin/env bash
# ABOUTME: Verification script for the AI workshop kind cluster.
# ABOUTME: Checks cluster health, node readiness, labels, and cert-manager status.

set -euo pipefail

CLUSTER_NAME="ai-workshop"
PASS=0
FAIL=0

# --- Helper functions --------------------------------------------------------

info()    { printf "\033[1;34m[INFO]\033[0m    %s\n" "$*"; }
pass()    { printf "\033[1;32m[PASS]\033[0m    %s\n" "$*"; PASS=$((PASS + 1)); }
fail_msg(){ printf "\033[1;31m[FAIL]\033[0m    %s\n" "$*"; FAIL=$((FAIL + 1)); }

# --- Check 1: Cluster exists and is reachable --------------------------------

info "Checking cluster '$CLUSTER_NAME'..."

if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    fail_msg "Kind cluster '$CLUSTER_NAME' does not exist. Run ./setup.sh first."
else
    pass "Kind cluster '$CLUSTER_NAME' exists."
fi

if kubectl cluster-info --context "kind-${CLUSTER_NAME}" >/dev/null 2>&1; then
    pass "kubectl can reach the cluster."
else
    fail_msg "kubectl cannot connect to the cluster."
fi

# --- Check 2: Nodes are Ready ------------------------------------------------

info "Checking node readiness..."

EXPECTED_NODES=3
READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null \
    | grep -c " Ready" || true)

if [[ "$READY_NODES" -eq "$EXPECTED_NODES" ]]; then
    pass "All $EXPECTED_NODES nodes are Ready."
else
    fail_msg "Expected $EXPECTED_NODES Ready nodes, found $READY_NODES."
fi

# --- Check 3: Worker labels ---------------------------------------------------

info "Checking worker node labels..."

GPU_LABELED=$(kubectl get nodes -l "node.kubernetes.io/gpu-type=simulated" \
    --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [[ "$GPU_LABELED" -eq 2 ]]; then
    pass "2 workers have gpu-type=simulated label."
else
    fail_msg "Expected 2 nodes with gpu-type=simulated, found $GPU_LABELED."
fi

ZONE_A=$(kubectl get nodes -l "topology.kubernetes.io/zone=zone-a" \
    --no-headers 2>/dev/null | wc -l | tr -d ' ')
ZONE_B=$(kubectl get nodes -l "topology.kubernetes.io/zone=zone-b" \
    --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [[ "$ZONE_A" -eq 1 && "$ZONE_B" -eq 1 ]]; then
    pass "Workers are in zone-a and zone-b."
else
    fail_msg "Expected 1 node in zone-a and 1 in zone-b (found $ZONE_A / $ZONE_B)."
fi

# --- Check 4: cert-manager pods are Running -----------------------------------

info "Checking cert-manager..."

CM_RUNNING=$(kubectl get pods -n cert-manager --no-headers 2>/dev/null \
    | grep -c "Running" || true)
if [[ "$CM_RUNNING" -ge 3 ]]; then
    pass "cert-manager has $CM_RUNNING running pods."
else
    fail_msg "cert-manager should have at least 3 running pods, found $CM_RUNNING."
fi

# --- Summary ------------------------------------------------------------------

echo ""
info "============================================"
info "Verification summary: $PASS passed, $FAIL failed"
info "============================================"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    info "Some checks failed. Review the output above and re-run ./setup.sh if needed."
    exit 1
fi

echo ""
info "Your environment is ready. Proceed to Lab 01!"
