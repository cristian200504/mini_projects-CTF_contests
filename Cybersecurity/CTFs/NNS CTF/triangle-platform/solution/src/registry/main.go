package main

import (
	"log"
	"os"
	"sort"
	"strings"

	"github.com/gofiber/fiber/v3"
	authenticationv1 "k8s.io/api/authentication/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	authenticationv1client "k8s.io/client-go/kubernetes/typed/authentication/v1"
	corev1client "k8s.io/client-go/kubernetes/typed/core/v1"
	"k8s.io/client-go/tools/clientcmd"
)

const (
	originNamespace = "triangle-origins"
	originPrefix    = "origin-"
)

type record struct {
	Host string   `json:"host"`
	Env  []string `json:"env"`
}

type server struct {
	origins corev1client.SecretInterface
	reviews authenticationv1client.TokenReviewInterface
}

func main() {
	config, err := clientcmd.BuildConfigFromFlags("", os.Getenv("KUBECONFIG"))
	if err != nil {
		log.Fatal(err)
	}
	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}

	s := &server{
		origins: client.CoreV1().Secrets(originNamespace),
		reviews: client.AuthenticationV1().TokenReviews(),
	}

	app := fiber.New(fiber.Config{
		AppName:      "triangle-registry",
		ServerHeader: "triangle",
	})
	app.Get("/internal/v1/domains", s.domains)
	log.Fatal(app.Listen(":8080", fiber.ListenConfig{DisableStartupMessage: true}))
}

func canonicalHost(host string) string {
	return strings.ToLower(strings.TrimSuffix(host, "."))
}

func (s *server) domains(c fiber.Ctx) error {
	header := c.Get(fiber.HeaderAuthorization)
	token := strings.TrimPrefix(header, "Bearer ")
	if token == "" || token == header {
		return c.SendStatus(fiber.StatusUnauthorized)
	}

	review, err := s.reviews.Create(c.RequestCtx(), &authenticationv1.TokenReview{
		Spec: authenticationv1.TokenReviewSpec{Token: token},
	}, metav1.CreateOptions{})
	if err != nil || !review.Status.Authenticated {
		return c.SendStatus(fiber.StatusUnauthorized)
	}
	if !allowedSubject(review.Status.User.Username) {
		return c.SendStatus(fiber.StatusForbidden)
	}

	host := canonicalHost(c.Query("host"))
	origin, err := s.origins.Get(c.RequestCtx(), originPrefix+host, metav1.GetOptions{})
	if apierrors.IsNotFound(err) {
		return c.SendStatus(fiber.StatusNotFound)
	}
	if err != nil {
		return c.SendStatus(fiber.StatusInternalServerError)
	}

	names := make([]string, 0, len(origin.Data))
	for name := range origin.Data {
		names = append(names, name)
	}
	sort.Strings(names)
	return c.JSON(record{Host: host, Env: names})
}

func allowedSubject(username string) bool {
	parts := strings.Split(username, ":")
	if len(parts) != 4 || parts[0] != "system" || parts[1] != "serviceaccount" {
		return false
	}
	return parts[3] == "tri-edge" || (parts[2] == "triangle-system" && parts[3] == "tri-registry-sync")
}
