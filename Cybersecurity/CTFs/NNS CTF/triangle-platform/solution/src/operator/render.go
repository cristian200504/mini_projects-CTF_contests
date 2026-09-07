package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

const (
	image          = "nginxinc/nginx-unprivileged:1.27-alpine"
	containerPort  = 8080
	tokenMountPath = "/var/run/triangle"
	originPath     = "/var/run/origin"
	tokenTTL       = 43200
)

const contentMountPath = "/srv/site"

func placeholder(name string) string {
	return fmt.Sprintf(`<!doctype html>
<meta charset="utf-8">
<title>%[1]s.sites.triangle.tld</title>
<style>
body { margin: 4rem auto; max-width: 30rem; background: #17171a; color: #e8e6e1;
       font: 15px/1.6 system-ui, sans-serif; }
p { color: #9a968f; font-size: 0.88rem; }
</style>
<h1>%[1]s.sites.triangle.tld</h1>
<p>This site is live. Set <code>content</code> in your site config to replace this page.</p>
`, name)
}

func nginxConf(cfg siteConfig) string {
	return fmt.Sprintf(`server {
    listen %d;
    root %s;
    index %s;

    location / {
        try_files $uri $uri/ =404;
    }
}
`, containerPort, cfg.Server.Root, cfg.Server.Index)
}

func siteOwner(site *unstructured.Unstructured) metav1.OwnerReference {
	return metav1.OwnerReference{
		APIVersion: siteGVK.GroupVersion().String(),
		Kind:       siteGVK.Kind,
		Name:       site.GetName(),
		UID:        site.GetUID(),
		Controller: ptr.To(true),
	}
}

func render(site *unstructured.Unstructured, cfg siteConfig, originSecret string) []client.Object {
	labels := map[string]string{"triangle.io/site": site.GetName()}
	meta := metav1.ObjectMeta{
		Name:            site.GetName(),
		Namespace:       site.GetNamespace(),
		Labels:          labels,
		OwnerReferences: []metav1.OwnerReference{siteOwner(site)},
	}

	page := cfg.Content
	if page == "" {
		page = placeholder(site.GetName())
	}

	configMap := &corev1.ConfigMap{
		TypeMeta:   metav1.TypeMeta{APIVersion: "v1", Kind: "ConfigMap"},
		ObjectMeta: meta,
		Data: map[string]string{
			"nginx.conf": nginxConf(cfg),
			"index.html": page,
		},
	}

	digest := sha256.Sum256([]byte(configMap.Data["nginx.conf"] + configMap.Data["index.html"]))

	deployment := &appsv1.Deployment{
		TypeMeta:   metav1.TypeMeta{APIVersion: "apps/v1", Kind: "Deployment"},
		ObjectMeta: meta,
		Spec: appsv1.DeploymentSpec{
			Replicas: ptr.To(int32(1)),
			Selector: &metav1.LabelSelector{MatchLabels: labels},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels:      labels,
					Annotations: map[string]string{"triangle.io/config": hex.EncodeToString(digest[:8])},
				},
				Spec: corev1.PodSpec{
					ServiceAccountName:           cfg.serviceAccountName(),
					AutomountServiceAccountToken: ptr.To(false),
					SecurityContext: &corev1.PodSecurityContext{
						RunAsNonRoot:   ptr.To(true),
						RunAsUser:      ptr.To(int64(101)),
						SeccompProfile: &corev1.SeccompProfile{Type: corev1.SeccompProfileTypeRuntimeDefault},
					},
					Containers: []corev1.Container{{
						Name:  "nginx",
						Image: image,
						Ports: []corev1.ContainerPort{{Name: "http", ContainerPort: containerPort}},
						SecurityContext: &corev1.SecurityContext{
							AllowPrivilegeEscalation: ptr.To(false),
							Capabilities:             &corev1.Capabilities{Drop: []corev1.Capability{"ALL"}},
						},
						VolumeMounts: []corev1.VolumeMount{
							{Name: "config", MountPath: "/etc/nginx/conf.d", ReadOnly: true},
							{Name: "content", MountPath: contentMountPath, ReadOnly: true},
							{Name: "triangle", MountPath: tokenMountPath, ReadOnly: true},
						},
					}},
					Volumes: []corev1.Volume{
						{
							Name: "config",
							VolumeSource: corev1.VolumeSource{
								ConfigMap: &corev1.ConfigMapVolumeSource{
									LocalObjectReference: corev1.LocalObjectReference{Name: site.GetName()},
									Items:                []corev1.KeyToPath{{Key: "nginx.conf", Path: "nginx.conf"}},
								},
							},
						},
						{
							Name: "content",
							VolumeSource: corev1.VolumeSource{
								ConfigMap: &corev1.ConfigMapVolumeSource{
									LocalObjectReference: corev1.LocalObjectReference{Name: site.GetName()},
									Items:                []corev1.KeyToPath{{Key: "index.html", Path: "index.html"}},
								},
							},
						},
						{
							Name: "triangle",
							VolumeSource: corev1.VolumeSource{
								Projected: &corev1.ProjectedVolumeSource{
									Sources: []corev1.VolumeProjection{{
										ServiceAccountToken: &corev1.ServiceAccountTokenProjection{
											Audience:          cfg.audience(),
											ExpirationSeconds: ptr.To(int64(tokenTTL)),
											Path:              "token",
										},
									}},
								},
							},
						},
					},
				},
			},
		},
	}

	if originSecret != "" {
		pod := &deployment.Spec.Template.Spec
		pod.Containers[0].VolumeMounts = append(pod.Containers[0].VolumeMounts,
			corev1.VolumeMount{Name: "origin", MountPath: originPath, ReadOnly: true})
		pod.Volumes = append(pod.Volumes, corev1.Volume{
			Name: "origin",
			VolumeSource: corev1.VolumeSource{
				Secret: &corev1.SecretVolumeSource{SecretName: originSecret},
			},
		})
	}

	service := &corev1.Service{
		TypeMeta:   metav1.TypeMeta{APIVersion: "v1", Kind: "Service"},
		ObjectMeta: meta,
		Spec: corev1.ServiceSpec{
			Selector: labels,
			Ports: []corev1.ServicePort{{
				Name:       "http",
				Port:       80,
				TargetPort: intstr.FromString("http"),
			}},
		},
	}

	return []client.Object{configMap, deployment, service}
}
