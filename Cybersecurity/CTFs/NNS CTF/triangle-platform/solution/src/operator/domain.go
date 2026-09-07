package main

import (
	"context"
	"sort"
	"strings"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

var domainGVK = schema.GroupVersionKind{Group: "triangle.io", Version: "v1", Kind: "Domain"}

const (
	platformZone    = "sites.triangle.tld"
	originNamespace = "triangle-origins"
	originPrefix    = "origin-"
)

func newDomain() *unstructured.Unstructured {
	domain := &unstructured.Unstructured{}
	domain.SetGroupVersionKind(domainGVK)
	return domain
}

func newDomainList() *unstructured.UnstructuredList {
	list := &unstructured.UnstructuredList{}
	list.SetGroupVersionKind(domainGVK.GroupVersion().WithKind(domainGVK.Kind + "List"))
	return list
}

func canonicalHost(host string) string {
	return strings.ToLower(strings.TrimSuffix(host, "."))
}

type claim struct {
	name string
	host string
	site types.NamespacedName
}

func claimsOf(list *unstructured.UnstructuredList) []claim {
	claims := make([]claim, 0, len(list.Items))
	for i := range list.Items {
		item := &list.Items[i]
		host, _, _ := unstructured.NestedString(item.Object, "spec", "host")
		namespace, _, _ := unstructured.NestedString(item.Object, "spec", "siteRef", "namespace")
		name, _, _ := unstructured.NestedString(item.Object, "spec", "siteRef", "name")
		if host == "" || namespace == "" || name == "" {
			continue
		}
		claims = append(claims, claim{
			name: item.GetName(),
			host: host,
			site: types.NamespacedName{Namespace: namespace, Name: name},
		})
	}
	sort.Slice(claims, func(i, j int) bool { return claims[i].name < claims[j].name })
	return claims
}

func contested(all []claim, c claim) bool {
	for _, other := range all {
		if other.name != c.name && other.host == c.host && other.site != c.site {
			return true
		}
	}
	return false
}

func serving(all []claim, site types.NamespacedName) []claim {
	served := []claim{}
	for _, c := range all {
		if c.site == site && !contested(all, c) {
			served = append(served, c)
		}
	}
	return served
}

func blocked(all []claim, site types.NamespacedName) []string {
	hosts := []string{}
	for _, c := range all {
		if c.site == site && contested(all, c) {
			hosts = append(hosts, c.host)
		}
	}
	return hosts
}

func domainToSite(_ context.Context, obj client.Object) []reconcile.Request {
	domain, ok := obj.(*unstructured.Unstructured)
	if !ok {
		return nil
	}
	namespace, _, _ := unstructured.NestedString(domain.Object, "spec", "siteRef", "namespace")
	name, _, _ := unstructured.NestedString(domain.Object, "spec", "siteRef", "name")
	if namespace == "" || name == "" {
		return nil
	}
	return []reconcile.Request{{NamespacedName: types.NamespacedName{Namespace: namespace, Name: name}}}
}

func (r *reconciler) claims(ctx context.Context) ([]claim, error) {
	list := newDomainList()
	if err := r.List(ctx, list); err != nil {
		return nil, err
	}
	return claimsOf(list), nil
}

func (r *reconciler) claimZoneHost(ctx context.Context, site *unstructured.Unstructured, all []claim) ([]claim, bool, error) {
	host := site.GetName() + "." + platformZone
	name := site.GetNamespace() + "-" + site.GetName()
	ref := types.NamespacedName{Namespace: site.GetNamespace(), Name: site.GetName()}

	for _, c := range all {
		if c.host == host && c.site != ref {
			return all, false, nil
		}
	}

	domain := newDomain()
	domain.SetName(name)
	if err := unstructured.SetNestedMap(domain.Object, map[string]interface{}{
		"host": host,
		"siteRef": map[string]interface{}{
			"namespace": site.GetNamespace(),
			"name":      site.GetName(),
		},
	}, "spec"); err != nil {
		return all, false, err
	}
	if err := r.Patch(ctx, domain, client.Apply, client.ForceOwnership, fieldOwner); err != nil {
		return all, false, err
	}

	for _, c := range all {
		if c.name == name {
			return all, true, nil
		}
	}
	return append(all, claim{name: name, host: host, site: ref}), true, nil
}

func (r *reconciler) syncOriginConfig(ctx context.Context, site *unstructured.Unstructured, served []claim) (string, error) {
	data := map[string][]byte{}
	for _, c := range served {
		source := &corev1.Secret{}
		key := client.ObjectKey{Namespace: originNamespace, Name: originPrefix + canonicalHost(c.host)}
		if err := r.Get(ctx, key, source); err != nil {
			if apierrors.IsNotFound(err) {
				continue
			}
			return "", err
		}
		for name, value := range source.Data {
			data[name] = value
		}
	}
	if len(data) == 0 {
		return "", nil
	}

	name := site.GetName() + "-origin"
	copied := &corev1.Secret{
		TypeMeta: metav1.TypeMeta{APIVersion: "v1", Kind: "Secret"},
		ObjectMeta: metav1.ObjectMeta{
			Name:            name,
			Namespace:       site.GetNamespace(),
			OwnerReferences: []metav1.OwnerReference{siteOwner(site)},
		},
		Data: data,
	}
	if err := r.Patch(ctx, copied, client.Apply, client.ForceOwnership, fieldOwner); err != nil {
		return "", err
	}
	return name, nil
}
