#!/bin/sh
set -eu

umask 077

wait_for() {
	n=0
	until "$@" >/dev/null 2>&1; do
		n=$((n + 1))
		if [ "$n" -ge 150 ]; then
			echo "timed out waiting for: $*" >&2
			exit 1
		fi
		sleep 2
	done
}

wait_for kubectl get --raw /readyz

kubectl apply -f /manifests/crd
kubectl wait --for=condition=Established --timeout=60s crd/sites.triangle.io crd/domains.triangle.io

kubectl apply --server-side --force-conflicts -k /manifests/kyverno
kubectl -n kyverno wait --for=condition=Available --timeout=600s deployment/kyverno-admission-controller

kubectl apply -f /manifests/policies
wait_for sh -c 'kubectl get validatingwebhookconfigurations -o yaml | grep -q triangle.io'

kubectl apply -f /manifests/bootstrap/namespaces.yaml

kubectl -n triangle-origins create secret generic origin-acme-invoices.sites.triangle.tld \
	--from-literal="FLAG=${FLAG}" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n triangle-origins create secret generic origin-myshop.sites.triangle.tld \
	--from-literal="SITE_LOCALE=nb-NO" --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f /manifests/bootstrap

wait_for kubectl -n tenant-b get deploy/invoices
kubectl -n tenant-b wait --for=condition=Available --timeout=300s deploy/invoices

kubectl -n tenant-a create token console --duration=24h | tr -d '\n' >/out/token
chown 1000:1000 /out/token
chmod 0600 /out/token
