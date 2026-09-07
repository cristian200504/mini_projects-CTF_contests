package main

import (
	"context"
	"log"
	"strings"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/klog/v2/textlogger"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"
)

const fieldOwner = client.FieldOwner("triangle-operator")

var siteGVK = schema.GroupVersionKind{Group: "triangle.io", Version: "v1", Kind: "Site"}

type reconciler struct {
	client.Client
}

func newSite() *unstructured.Unstructured {
	site := &unstructured.Unstructured{}
	site.SetGroupVersionKind(siteGVK)
	return site
}

func (r *reconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	site := newSite()
	if err := r.Get(ctx, req.NamespacedName, site); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	siteYAML, _, err := unstructured.NestedString(site.Object, "spec", "siteYAML")
	if err != nil {
		return ctrl.Result{}, err
	}

	cfg, err := decodeSite(siteYAML)
	if err != nil {
		return ctrl.Result{}, r.setStatus(ctx, site, "Error", errInvalidSite.Error())
	}

	all, err := r.claims(ctx)
	if err != nil {
		return ctrl.Result{}, err
	}
	all, claimed, err := r.claimZoneHost(ctx, site, all)
	if err != nil {
		return ctrl.Result{}, err
	}
	key := types.NamespacedName{Namespace: site.GetNamespace(), Name: site.GetName()}
	origin, err := r.syncOriginConfig(ctx, site, serving(all, key))
	if err != nil {
		return ctrl.Result{}, err
	}

	for _, obj := range render(site, cfg, origin) {
		if err := r.Patch(ctx, obj, client.Apply, client.ForceOwnership, fieldOwner); err != nil {
			return ctrl.Result{}, err
		}
	}
	disputed := blocked(all, key)
	if !claimed {
		disputed = append(disputed, site.GetName()+"."+platformZone)
	}
	if len(disputed) > 0 {
		return ctrl.Result{}, r.setStatus(ctx, site, "Ready",
			"site rendered; hostname claimed by another site: "+strings.Join(disputed, ", "))
	}
	return ctrl.Result{}, r.setStatus(ctx, site, "Ready", "site rendered")
}

func (r *reconciler) setStatus(ctx context.Context, site *unstructured.Unstructured, phase, message string) error {
	status := map[string]interface{}{"phase": phase, "message": message}
	if err := unstructured.SetNestedMap(site.Object, status, "status"); err != nil {
		return err
	}
	return r.Status().Update(ctx, site)
}

func main() {
	ctrl.SetLogger(textlogger.NewLogger(textlogger.NewConfig()))

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{Metrics: metricsserver.Options{BindAddress: "0"}})
	if err != nil {
		log.Fatal(err)
	}
	err = ctrl.NewControllerManagedBy(mgr).
		For(newSite()).
		Watches(newDomain(), handler.EnqueueRequestsFromMapFunc(domainToSite)).
		Complete(&reconciler{mgr.GetClient()})
	if err != nil {
		log.Fatal(err)
	}
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		log.Fatal(err)
	}
}
