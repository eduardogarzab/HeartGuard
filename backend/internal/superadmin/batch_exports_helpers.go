package superadmin

import (
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"os"
	"path/filepath"
	"strings"
	"unicode"

	"github.com/google/uuid"
)

const batchExportUploadDir = "uploads/batch_exports"

const maxBatchExportUploadSize = 50 << 20 // 50 MiB

var (
	errBatchExportMissingFile  = errors.New("missing batch export file")
	errBatchExportFileTooLarge = errors.New("batch export file too large")
)

func sanitizeBatchExportBase(name string) string {
	base := strings.TrimSpace(filepath.Base(name))
	if base == "" || base == "." || base == string(filepath.Separator) {
		return "export"
	}
	base = strings.TrimSuffix(base, filepath.Ext(base))
	if base == "" {
		return "export"
	}
	var b strings.Builder
	for _, r := range base {
		switch {
		case unicode.IsLetter(r) || unicode.IsDigit(r):
			b.WriteRune(unicode.ToLower(r))
		case r == '-' || r == '_':
			b.WriteRune(r)
		case unicode.IsSpace(r):
			b.WriteRune('-')
		}
	}
	cleaned := strings.Trim(b.String(), "-_")
	if cleaned == "" {
		return "export"
	}
	if len(cleaned) > 40 {
		cleaned = cleaned[:40]
	}
	return cleaned
}

func saveBatchExportUpload(header *multipart.FileHeader) (string, error) {
	if header == nil {
		return "", errBatchExportMissingFile
	}
	src, err := header.Open()
	if err != nil {
		return "", err
	}
	defer src.Close()

	if err := os.MkdirAll(batchExportUploadDir, 0o755); err != nil {
		return "", err
	}

	ext := strings.ToLower(filepath.Ext(header.Filename))
	base := sanitizeBatchExportBase(header.Filename)
	filename := fmt.Sprintf("%s_%s%s", base, uuid.NewString(), ext)
	destPath := filepath.Join(batchExportUploadDir, filename)

	dest, err := os.Create(destPath)
	if err != nil {
		return "", err
	}
	defer func() {
		_ = dest.Close()
	}()

	limited := io.LimitReader(src, maxBatchExportUploadSize+1)
	written, err := io.Copy(dest, limited)
	if err != nil {
		_ = os.Remove(destPath)
		return "", err
	}
	if written > maxBatchExportUploadSize {
		_ = os.Remove(destPath)
		return "", errBatchExportFileTooLarge
	}

	return "file://" + filepath.ToSlash(destPath), nil
}
