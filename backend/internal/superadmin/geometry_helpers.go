package superadmin

import (
	"encoding/hex"
	"fmt"
	"strings"
	"unicode"
)

func decodeWKBHex(raw string) ([]byte, error) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return nil, nil
	}
	trimmed = strings.TrimPrefix(trimmed, "0x")
	trimmed = strings.TrimPrefix(trimmed, "0X")
	trimmed = strings.TrimPrefix(trimmed, "\\x")
	trimmed = strings.TrimPrefix(trimmed, "\\X")

	var builder strings.Builder
	builder.Grow(len(trimmed))
	for _, r := range trimmed {
		if unicode.IsSpace(r) {
			continue
		}
		builder.WriteRune(r)
	}
	normalized := builder.String()
	if normalized == "" {
		return nil, nil
	}
	if len(normalized)%2 != 0 {
		return nil, fmt.Errorf("invalid hex length")
	}
	data, err := hex.DecodeString(normalized)
	if err != nil {
		return nil, err
	}
	return data, nil
}
