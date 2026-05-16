package main

import (
	"fmt"
	"strings"
	"regexp"
)

func main() {
	fmt.Println("ſcript vs script:", strings.EqualFold("ſcript", "script"))
	
	tagRE := regexp.MustCompile(`(?is)<\s*(/?)\s*([^\s>/]+)([^>]*)>`)
	input := `<ſcript src="http://example.com/xss.js"></ſcript>`
	
	output := tagRE.ReplaceAllStringFunc(input, func(raw string) string {
		match := tagRE.FindStringSubmatch(raw)
		if len(match) != 4 {
			return raw
		}
		
		name := strings.TrimSpace(match[2])
		if strings.EqualFold(name, "script") {
			return "<script" + match[3] + ">"
		}
		return raw
	})
	fmt.Println("Output:", output)
}
