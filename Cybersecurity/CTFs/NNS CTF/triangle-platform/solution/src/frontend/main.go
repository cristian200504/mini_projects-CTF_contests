package main

import (
	"crypto/tls"
	"embed"
	"io/fs"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
	"time"
)

//go:embed www
var assets embed.FS

const (
	listenAddr  = ":7681"
	apiServer   = "https://127.0.0.1:6443"
	registryURL = "http://127.0.0.1:8080"
	tokenPath   = "/out/token"
)

func main() {
	token, err := os.ReadFile(tokenPath)
	if err != nil {
		log.Fatal(err)
	}

	www, err := fs.Sub(assets, "www")
	if err != nil {
		log.Fatal(err)
	}

	api := proxy(apiServer)
	api.Transport = &http.Transport{TLSClientConfig: &tls.Config{InsecureSkipVerify: true}}
	api.FlushInterval = -1

	director := api.Director
	tenant := "Bearer " + strings.TrimSpace(string(token))
	api.Director = func(r *http.Request) {
		director(r)
		if r.Header.Get("Authorization") == "" {
			r.Header.Set("Authorization", tenant)
		}
	}

	mux := http.NewServeMux()
	mux.Handle("/internal/", proxy(registryURL))
	mux.Handle("/", console(www, api))

	server := &http.Server{
		Addr:              listenAddr,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}
	log.Fatal(server.ListenAndServe())
}

func proxy(target string) *httputil.ReverseProxy {
	u, err := url.Parse(target)
	if err != nil {
		log.Fatal(err)
	}
	return httputil.NewSingleHostReverseProxy(u)
}

func console(www fs.FS, api http.Handler) http.Handler {
	files := http.FileServer(http.FS(www))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		name := strings.TrimPrefix(r.URL.Path, "/")
		if name == "" {
			name = "index.html"
		}
		if _, err := fs.Stat(www, name); err == nil {
			files.ServeHTTP(w, r)
			return
		}
		api.ServeHTTP(w, r)
	})
}
