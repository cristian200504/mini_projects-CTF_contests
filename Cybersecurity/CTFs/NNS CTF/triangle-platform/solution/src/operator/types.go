package main

import (
	"errors"
	"regexp"

	"gopkg.in/yaml.v3"
)

type Plane string

type Target struct {
	Plane Plane `yaml:"plane"`
}

type Integration string

type serverConfig struct {
	Root  string `yaml:"root"`
	Index string `yaml:"index"`
}

type siteConfig struct {
	Target       Target
	Integrations []Integration
	Server       serverConfig
	Content      string
}

var integrationAccounts = map[Integration]string{
	"forms":     "tri-forms",
	"analytics": "tri-analytics",
	"images":    "tri-images",
	"edge":      "tri-edge",
}

var planeAudiences = map[Plane]string{
	"origin":  "triangle.origin.v1",
	"edge":    "triangle.edge.v1",
	"control": "",
}

const siteSegment = `[a-zA-Z0-9][a-zA-Z0-9._-]*`

var (
	siteRoot  = regexp.MustCompile(`^(/` + siteSegment + `)+$`)
	siteIndex = regexp.MustCompile(`^` + siteSegment + `$`)
)

var errInvalidSite = errors.New("site configuration is invalid")

func platformDefaults() siteConfig {
	return siteConfig{
		Target: Target{Plane: "control"},
		Server: serverConfig{Root: "/srv/site", Index: "index.html"},
	}
}

func (t *Target) UnmarshalYAML(node *yaml.Node) error {
	var aux struct {
		Plane string `yaml:"plane"`
	}
	if err := node.Decode(&aux); err != nil {
		return errInvalidSite
	}
	if aux.Plane != "origin" && aux.Plane != "edge" {
		return errInvalidSite
	}
	t.Plane = Plane(aux.Plane)
	return nil
}

func (i *Integration) UnmarshalYAML(node *yaml.Node) error {
	var name string
	if err := node.Decode(&name); err != nil {
		return errInvalidSite
	}
	if _, ok := integrationAccounts[Integration(name)]; !ok {
		return errInvalidSite
	}
	*i = Integration(name)
	return nil
}

func (s serverConfig) validate() error {
	if !siteRoot.MatchString(s.Root) || !siteIndex.MatchString(s.Index) {
		return errInvalidSite
	}
	return nil
}

func decodeSite(siteYAML string) (siteConfig, error) {
	site := platformDefaults()

	var nodes map[string]yaml.Node
	if err := yaml.Unmarshal([]byte(siteYAML), &nodes); err != nil {
		return site, errInvalidSite
	}

	target, ok := nodes["target"]
	if !ok {
		return site, errInvalidSite
	}
	if err := target.Decode(&site.Target); err != nil {
		return site, errInvalidSite
	}

	if integrations, ok := nodes["integrations"]; ok {
		if err := integrations.Decode(&site.Integrations); err != nil {
			return site, errInvalidSite
		}
		if integrations.Kind == yaml.SequenceNode && len(site.Integrations) != len(integrations.Content) {
			return site, errInvalidSite
		}
	}
	if content, ok := nodes["content"]; ok {
		if err := content.Decode(&site.Content); err != nil {
			return site, errInvalidSite
		}
	}
	if server, ok := nodes["server"]; ok {
		if err := server.Decode(&site.Server); err != nil {
			return site, errInvalidSite
		}
	}
	if err := site.Server.validate(); err != nil {
		return site, err
	}
	if _, ok := planeAudiences[site.Target.Plane]; !ok {
		return site, errInvalidSite
	}
	return site, nil
}

func (c siteConfig) serviceAccountName() string {
	if len(c.Integrations) == 0 {
		return "tri-forms"
	}
	return integrationAccounts[c.Integrations[0]]
}

func (c siteConfig) audience() string {
	return planeAudiences[c.Target.Plane]
}
