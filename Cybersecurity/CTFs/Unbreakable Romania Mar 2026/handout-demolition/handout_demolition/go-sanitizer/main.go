package main

import (
	"encoding/json"
	"html"
	"io"
	"log"
	"net/http"
	"regexp"
	"strings"
)

var tagRE = regexp.MustCompile(`(?is)<\s*(/?)\s*([^\s>/]+)([^>]*)>`)

type sanitizeRequest struct {
	HTML     string   `json:"html"`
	Allow    []string `json:"allow"`
	Mode     string   `json:"mode"`
	Switches []string `json:"switches"`
}

type sanitizeResponse struct {
	HTML  string `json:"html"`
	Mode  string `json:"mode"`
	Count int    `json:"count"`
}

func canonicalTag(name string, allow []string) string {
	for _, candidate := range allow {
		if strings.EqualFold(name, candidate) {
			return candidate
		}
	}
	return ""
}

func sanitizeMarkup(input string, allow []string) (string, int) {
	changes := 0
	output := tagRE.ReplaceAllStringFunc(input, func(raw string) string {
		match := tagRE.FindStringSubmatch(raw)
		if len(match) != 4 {
			return html.EscapeString(raw)
		}

		slash := strings.TrimSpace(match[1])
		name := strings.TrimSpace(match[2])
		attrs := match[3]

		canon := canonicalTag(name, allow)
		if canon == "" {
			return html.EscapeString(raw)
		}

		changes++
		if slash != "" {
			return "</" + canon + ">"
		}
		return "<" + canon + attrs + ">"
	})

	return output, changes
}

func handleSanitize(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	defer r.Body.Close()
	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
	if err != nil {
		http.Error(w, "read error", http.StatusBadRequest)
		return
	}

	var req sanitizeRequest
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}

	if len(req.Allow) == 0 {
		req.Allow = []string{"script"}
	}

	mode := req.Mode
	if mode == "" {
		mode = "legacy"
	}

	sanitized, changed := sanitizeMarkup(req.HTML, req.Allow)
	resp := sanitizeResponse{HTML: sanitized, Mode: mode, Count: changed}

	w.Header().Set("Content-Type", "application/json")
	enc := json.NewEncoder(w)
	_ = enc.Encode(resp)
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/sanitize", handleSanitize)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	server := &http.Server{
		Addr:    "127.0.0.1:7071",
		Handler: mux,
	}

	log.Fatal(server.ListenAndServe())
}
