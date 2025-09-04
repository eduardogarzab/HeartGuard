package main

import (
	"database/sql"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
)

var db *sql.DB

func main() {
	var err error
	connStr := "user=postgres password=heartguard1234 dbname=heartguard sslmode=disable"
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}

	router := gin.Default()
	router.LoadHTMLGlob("templates/*")
	router.Static("/static", "./static")

	// Vistas HTML
	router.GET("/login", func(c *gin.Context) {
		c.HTML(http.StatusOK, "login.html", nil)
	})
	router.GET("/admin", func(c *gin.Context) {
		c.HTML(http.StatusOK, "admin_dashboard.html", nil)
	})

	// Endpoints
	router.POST("/login", login) // login exclusivo admin
	router.POST("/admin/:org_id/pacientes", altaPaciente)
	router.GET("/admin/:org_id/pacientes", listarPacientes)
	router.PUT("/admin/:org_id/pacientes/:id", actualizarPaciente)
	router.DELETE("/admin/:org_id/pacientes/:id", eliminarPaciente)

	router.Run(":8080")
}

//
// ===== Handlers =====
//

// Login exclusivo del administrador
func login(c *gin.Context) {
	var data struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}
	if err := c.BindJSON(&data); err != nil {
		c.JSON(400, gin.H{"error": "invalid request"})
		return
	}

	var patientID, orgID int
	var hash string
	var isAdmin bool
	err := db.QueryRow(
		"SELECT patient_id, password_hash, is_admin, org_id FROM pacientes WHERE username=$1",
		data.Username,
	).Scan(&patientID, &hash, &isAdmin, &orgID)

	if err != nil {
		c.JSON(401, gin.H{"error": "usuario no encontrado"})
		return
	}

	if bcrypt.CompareHashAndPassword([]byte(hash), []byte(data.Password)) != nil {
		c.JSON(401, gin.H{"error": "contraseña incorrecta"})
		return
	}

	if !isAdmin {
		c.JSON(403, gin.H{"error": "acceso denegado: solo administradores"})
		return
	}

	c.JSON(200, gin.H{
		"status":   "ok",
		"user_id":  patientID,
		"role":     "admin",
		"org_id":   orgID,
	})
}

// Alta paciente (solo admin, is_admin siempre false)
func altaPaciente(c *gin.Context) {
	orgID := c.Param("org_id")

	var data struct {
		Nombre   string  `json:"nombre"`
		Edad     int     `json:"edad"`
		Sexo     string  `json:"sexo"`
		Altura   float64 `json:"altura_cm"`
		Peso     float64 `json:"peso_kg"`
		Username string  `json:"username"`
		Password string  `json:"password"`
	}
	if err := c.BindJSON(&data); err != nil {
		c.JSON(400, gin.H{"error": "invalid request"})
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(data.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(500, gin.H{"error": "error al generar hash"})
		return
	}

	_, err = db.Exec(
		"INSERT INTO pacientes (org_id, nombre, edad, sexo, altura_cm, peso_kg, username, password_hash, is_admin) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,false)",
		orgID, data.Nombre, data.Edad, data.Sexo, data.Altura, data.Peso, data.Username, string(hash),
	)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}

	c.JSON(201, gin.H{"status": "Paciente creado"})
}

// Listar pacientes de una organización
func listarPacientes(c *gin.Context) {
	orgID := c.Param("org_id")

	rows, err := db.Query(
		"SELECT patient_id, nombre, edad, sexo, altura_cm, peso_kg, username FROM pacientes WHERE org_id=$1 AND is_admin=false ORDER BY patient_id",
		orgID,
	)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var result []map[string]interface{}
	for rows.Next() {
		var id, edad int
		var nombre, sexo, username string
		var altura, peso float64
		rows.Scan(&id, &nombre, &edad, &sexo, &altura, &peso, &username)
		result = append(result, gin.H{
			"id":       id,
			"nombre":   nombre,
			"edad":     edad,
			"sexo":     sexo,
			"altura":   altura,
			"peso":     peso,
			"username": username,
		})
	}
	c.JSON(200, result)
}

// Actualizar paciente (excepto admin)
func actualizarPaciente(c *gin.Context) {
	orgID := c.Param("org_id")
	id := c.Param("id")

	// Estructura de datos de entrada
	var data struct {
		Nombre   *string  `json:"nombre"`
		Edad     *int     `json:"edad"`
		Sexo     *string  `json:"sexo"`
		Altura   *float64 `json:"altura_cm"`
		Peso     *float64 `json:"peso_kg"`
		Username *string  `json:"username"`
		Password *string  `json:"password"`
	}
	if err := c.BindJSON(&data); err != nil {
		c.JSON(400, gin.H{"error": "invalid request"})
		return
	}

	// Traer valores actuales de la BD
	var nombre, sexo, username string
	var edad int
	var altura, peso float64
	err := db.QueryRow(
		"SELECT nombre, edad, sexo, altura_cm, peso_kg, username FROM pacientes WHERE patient_id=$1 AND org_id=$2 AND is_admin=false",
		id, orgID,
	).Scan(&nombre, &edad, &sexo, &altura, &peso, &username)
	if err != nil {
		c.JSON(404, gin.H{"error": "Paciente no encontrado"})
		return
	}

	// Usar nuevos valores si vienen en la request
	if data.Nombre != nil {
		nombre = *data.Nombre
	}
	if data.Edad != nil {
		edad = *data.Edad
	}
	if data.Sexo != nil {
		sexo = *data.Sexo
	}
	if data.Altura != nil {
		altura = *data.Altura
	}
	if data.Peso != nil {
		peso = *data.Peso
	}
	if data.Username != nil {
		username = *data.Username
	}

	// Si hay nueva contraseña → re-hashear
	if data.Password != nil && *data.Password != "" {
		hash, _ := bcrypt.GenerateFromPassword([]byte(*data.Password), bcrypt.DefaultCost)
		_, err = db.Exec(
			"UPDATE pacientes SET nombre=$1, edad=$2, sexo=$3, altura_cm=$4, peso_kg=$5, username=$6, password_hash=$7 WHERE patient_id=$8 AND org_id=$9 AND is_admin=false",
			nombre, edad, sexo, altura, peso, username, string(hash), id, orgID,
		)
	} else {
		_, err = db.Exec(
			"UPDATE pacientes SET nombre=$1, edad=$2, sexo=$3, altura_cm=$4, peso_kg=$5, username=$6 WHERE patient_id=$7 AND org_id=$8 AND is_admin=false",
			nombre, edad, sexo, altura, peso, username, id, orgID,
		)
	}
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}

	c.JSON(200, gin.H{"status": "Paciente actualizado"})
}


// Eliminar paciente (excepto admin)
func eliminarPaciente(c *gin.Context) {
	orgID := c.Param("org_id")
	id := c.Param("id")

	_, err := db.Exec("DELETE FROM pacientes WHERE patient_id=$1 AND org_id=$2 AND is_admin=false", id, orgID)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"status": "Paciente eliminado"})
}
