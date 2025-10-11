package ui

import (
	"bytes"
	"encoding/json"
	"html/template"
	"io/fs"
	"net/http"
	"net/url"
	"path/filepath"
	"strconv"
	"time"

	"heartguard-superadmin/internal/models"
	"heartguard-superadmin/internal/session"
)

type Renderer struct {
	templates *template.Template
}

type Breadcrumb struct {
	Label string
	URL   string
}

type ViewData struct {
	Title           string
	CSRFToken       string
	Flashes         []session.Flash
	CurrentUser     *models.User
	Settings        *models.SystemSettings
	Data            any
	Breadcrumbs     []Breadcrumb
	IsSuperadmin    bool
	ContentTemplate string
	ContentHTML     template.HTML
}

func NewRenderer() (*Renderer, error) {
	funcMap := template.FuncMap{
		"formatTime": func(t time.Time) string {
			if t.IsZero() {
				return ""
			}
			return t.Local().Format("2006-01-02 15:04")
		},
		"formatTimePtr": func(t *time.Time) string {
			if t == nil {
				return ""
			}
			return t.In(time.Local).Format("2006-01-02 15:04")
		},
		"formatTimeLocal": func(t time.Time) string {
			if t.IsZero() {
				return ""
			}
			return t.In(time.Local).Format("2006-01-02T15:04")
		},
		"formatTimeLocalPtr": func(t *time.Time) string {
			if t == nil {
				return ""
			}
			return t.In(time.Local).Format("2006-01-02T15:04")
		},
		"formatDate": func(t time.Time) string {
			if t.IsZero() {
				return ""
			}
			return t.In(time.Local).Format("2006-01-02")
		},
		"formatDatePtr": func(t *time.Time) string {
			if t == nil {
				return ""
			}
			return t.In(time.Local).Format("2006-01-02")
		},
		"formatFloat32": func(v *float32) string {
			if v == nil {
				return ""
			}
			return strconv.FormatFloat(float64(*v), 'f', 4, 32)
		},
		"formatFloat64": func(v *float64, prec int) string {
			if v == nil {
				return ""
			}
			if prec < 0 {
				prec = 2
			}
			return strconv.FormatFloat(*v, 'f', prec, 64)
		},
		"stringValue": func(ptr *string) string {
			if ptr == nil {
				return ""
			}
			return *ptr
		},
		"urlquery": url.QueryEscape,
		"hasScope": func(scopes []string, code string) bool {
			for _, s := range scopes {
				if s == code {
					return true
				}
			}
			return false
		},
		"formatIntPtr": func(v *int) string {
			if v == nil {
				return ""
			}
			return strconv.Itoa(*v)
		},
		"toJSON": func(v any) template.JS {
			b, err := json.Marshal(v)
			if err != nil {
				return template.JS("null")
			}
			return template.JS(b)
		},
	}
	root := template.New("root").Funcs(funcMap)
	var files []string
	err := filepath.WalkDir("templates", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if filepath.Ext(path) == ".html" {
			files = append(files, path)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	if len(files) == 0 {
		return nil, fs.ErrNotExist
	}
	parsed, err := root.ParseFiles(files...)
	if err != nil {
		return nil, err
	}
	return &Renderer{templates: parsed}, nil
}

func (r *Renderer) Render(w http.ResponseWriter, name string, data ViewData) error {
	if data.ContentTemplate != "" {
		buf := new(bytes.Buffer)
		if err := r.templates.ExecuteTemplate(buf, data.ContentTemplate, data); err != nil {
			return err
		}
		data.ContentHTML = template.HTML(buf.String())
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	return r.templates.ExecuteTemplate(w, name, data)
}
