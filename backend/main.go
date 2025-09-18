package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	_ "github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
)

// Variables globales
var db *sql.DB

// Estructuras de datos (normalizadas)
type Usuario struct {
	ID                  int       `json:"id"`
	Nombre              string    `json:"nombre"`
	Email               string    `json:"email"`
	Rol                 string    `json:"rol"` // Nombre del rol
	Latitud             *float64  `json:"latitud,omitempty"`
	Longitud            *float64  `json:"longitud,omitempty"`
	UltimaActualizacion *time.Time `json:"ultima_actualizacion,omitempty"`
	FechaCreacion       time.Time `json:"fecha_creacion"`
	NombreFamilia       *string   `json:"nombre_familia,omitempty"`
	Relacion            *string   `json:"relacion,omitempty"`
}

type Familia struct {
	ID            int       `json:"id"`
	NombreFamilia string    `json:"nombre_familia"`
	FechaCreacion time.Time `json:"fecha_creacion"`
	TotalMiembros int       `json:"total_miembros,omitempty"`
}

type Ubicacion struct {
	ID        int       `json:"id"`
	UsuarioID int       `json:"usuario_id"`
	Latitud   float64   `json:"latitud"`
	Longitud  float64   `json:"longitud"`
	Timestamp time.Time `json:"timestamp"`
}

type Metrica struct {
	ID                int       `json:"id"`
	UsuarioID         int       `json:"usuario_id"`
	FrecuenciaCardiaca *int     `json:"frecuencia_cardiaca,omitempty"`
	Oxigenacion       *int     `json:"oxigenacion,omitempty"`
	PresionSistolica  *int     `json:"presion_sistolica,omitempty"`
	PresionDiastolica *int     `json:"presion_diastolica,omitempty"`
	Actividad         *string  `json:"actividad,omitempty"`
	Timestamp         time.Time `json:"timestamp"`
}


type EstadisticasSistema struct {
	TotalMiembros        int `json:"total_miembros"`
	TotalFamilias        int `json:"total_familias"`
	AlertasPendientes    int `json:"alertas_pendientes"`
	MicroserviciosActivos int `json:"microservicios_activos"`
	MetricasHoy          int `json:"metricas_hoy"`
}

// Estructuras para requests
type LoginRequest struct {
	Email    string `json:"email" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type CreateUsuarioRequest struct {
	Nombre    string `json:"nombre" binding:"required"`
	Email     string `json:"email" binding:"required"`
	Password  string `json:"password" binding:"required"`
	Rol       string `json:"rol" binding:"required"`
	FamiliaID *int   `json:"familia_id,omitempty"`
}

type UpdateUsuarioRequest struct {
	Nombre    *string `json:"nombre,omitempty"`
	Email     *string `json:"email,omitempty"`
	Rol       *string `json:"rol,omitempty"`
	FamiliaID *int    `json:"familia_id,omitempty"`
}

type CreateFamiliaRequest struct {
	NombreFamilia string `json:"nombre_familia" binding:"required"`
}

type CreateMetricaRequest struct {
	UsuarioID         int     `json:"usuario_id" binding:"required"`
	FrecuenciaCardiaca *int   `json:"frecuencia_cardiaca,omitempty"`
	Oxigenacion       *int   `json:"oxigenacion,omitempty"`
	PresionSistolica  *int   `json:"presion_sistolica,omitempty"`
	PresionDiastolica *int   `json:"presion_diastolica,omitempty"`
	Actividad         *string `json:"actividad,omitempty"`
}


func main() {
	// Configuración de la base de datos
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbUser := getEnv("DB_USER", "heartguard")
	dbPassword := getEnv("DB_PASSWORD", "heartguard123")
	dbName := getEnv("DB_NAME", "heartguard")

	// Conectar a la base de datos
	dbURL := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	var err error
	db, err = sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal("Error conectando a la base de datos:", err)
	}
	defer db.Close()

	// Verificar la conexión
	if err = db.Ping(); err != nil {
		log.Fatal("Error verificando conexión a la base de datos:", err)
	}

	fmt.Println("✅ Conexión a la base de datos establecida correctamente")

	// Configurar Gin
	r := gin.Default()

	// Middleware CORS
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")
		
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Servir archivos estáticos
	r.Static("/static", "./static")
	
	// Cargar templates HTML
	r.LoadHTMLGlob("templates/*")

	// Ruta principal - Dashboard web
	r.GET("/", func(c *gin.Context) {
		c.HTML(200, "index.html", gin.H{})
	})
	
	// Ruta de API info
	r.GET("/api", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "HeartGuard SuperAdmin Backend",
			"version": "1.0.0",
			"status":  "running",
			"web_dashboard": "http://localhost:8080",
		})
	})

	// API de autenticación
	api := r.Group("/admin")
	{
		api.POST("/login", login)
		api.POST("/logout", logout)
		
		// Rutas protegidas para superadministrador
		protected := api.Group("/")
		protected.Use(authMiddleware())
		{
			// Dashboard y estadísticas
			protected.GET("/dashboard", getDashboardStats)
			
			// CRUD Usuarios
			protected.GET("/usuarios", getUsuarios)
			protected.POST("/usuarios", createUsuario)
			protected.GET("/usuarios/:id", getUsuario)
			protected.PUT("/usuarios/:id", updateUsuario)
			protected.DELETE("/usuarios/:id", deleteUsuario)
			
			// CRUD Familias
			protected.GET("/familias", getFamilias)
			protected.POST("/familias", createFamilia)
			protected.GET("/familias/:id", getFamilia)
			protected.PUT("/familias/:id", updateFamilia)
			protected.DELETE("/familias/:id", deleteFamilia)
			
			// Asignación de usuarios a familias
			protected.POST("/familias/asignar", asignarUsuarioFamilia)
			protected.POST("/familias/remover", removerUsuarioFamilia)
			
			
			// CRUD Alertas
			protected.GET("/alertas", getAlertas)
			protected.POST("/alertas", createAlerta)
			protected.PUT("/alertas/:id/atender", atenderAlerta)
			protected.DELETE("/alertas/:id", deleteAlerta)
			
			// CRUD Catálogos
			protected.GET("/catalogos", getCatalogos)
			protected.GET("/catalogos/:id", getCatalogo)
			protected.POST("/catalogos", createCatalogo)
			protected.PUT("/catalogos/:id", updateCatalogo)
			protected.DELETE("/catalogos/:id", deleteCatalogo)
			
			// Logs del sistema
			protected.GET("/logs", getLogsSistema)
			
			// Monitoreo de microservicios
			protected.GET("/microservicios", getHealthMicroservicios)
			protected.PUT("/microservicios/:id/estado", updateEstadoMicroservicio)
		}
	}

	// Iniciar servidor
	port := getEnv("PORT", "8080")
	fmt.Printf("🚀 Servidor HeartGuard SuperAdmin iniciado en http://localhost:%s\n", port)
	fmt.Printf("🔗 API REST: http://localhost:%s/admin\n", port)
	
	if err := r.Run(":" + port); err != nil {
		log.Fatal("Error iniciando servidor:", err)
	}
}

// =========================================================
// FUNCIONES DE AUTENTICACIÓN
// =========================================================

func login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos de entrada inválidos"})
		return
	}

	// Buscar superadministrador en la base de datos (estructura normalizada)
	var usuario Usuario
	var passwordHash string
	var rolID int
	query := `SELECT u.id, u.nombre, u.email, u.rol_id, u.latitud, u.longitud, 
			  u.ultima_actualizacion, u.fecha_creacion, u.password_hash,
			  r.nombre as rol_nombre
			  FROM usuarios u
			  JOIN roles r ON u.rol_id = r.id
			  WHERE u.email = $1 AND r.nombre = 'superadmin'`
	
	err := db.QueryRow(query, req.Email).Scan(
		&usuario.ID, &usuario.Nombre, &usuario.Email, &rolID, 
		&usuario.Latitud, &usuario.Longitud,
		&usuario.UltimaActualizacion, &usuario.FechaCreacion, 
		&passwordHash, &usuario.Rol,
	)

	if err != nil {
		log.Printf("Error buscando superadmin %s: %v", req.Email, err)
		c.JSON(401, gin.H{"error": "Credenciales inválidas"})
		return
	}

	// Verificar contraseña
	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password)); err != nil {
		log.Printf("Error verificando contraseña: %v", err)
		c.JSON(401, gin.H{"error": "Credenciales inválidas"})
		return
	}

	// Generar JWT
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"usuario_id": usuario.ID,
		"email":      usuario.Email,
		"rol":        usuario.Rol,
		"exp":        time.Now().Add(time.Hour * 24).Unix(),
	})

	tokenString, err := token.SignedString([]byte(getEnv("JWT_SECRET", "heartguard-superadmin-secret-key-123")))
	if err != nil {
		c.JSON(500, gin.H{"error": "Error generando token"})
		return
	}

	// Actualizar último acceso
	updateQuery := `UPDATE usuarios SET ultima_actualizacion = CURRENT_TIMESTAMP WHERE id = $1`
	db.Exec(updateQuery, usuario.ID)

	// Log de login exitoso
	fmt.Printf("✅ Login exitoso para usuario: %s\n", usuario.Email)

	c.JSON(200, gin.H{
		"success": true,
		"token":   tokenString,
		"usuario": usuario,
		"message": "Login exitoso",
	})
}

func logout(c *gin.Context) {
	// Obtener información del usuario del token
	usuarioID, exists := c.Get("usuario_id")
	if !exists {
		c.JSON(401, gin.H{"error": "Token inválido"})
		return
	}

	// Log de logout exitoso
	fmt.Printf("✅ Logout exitoso para usuario ID: %v\n", usuarioID)

	c.JSON(200, gin.H{"message": "Logout exitoso"})
}

// =========================================================
// MIDDLEWARE DE AUTENTICACIÓN
// =========================================================

func authMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.GetHeader("Authorization")
		if tokenString == "" {
			c.JSON(401, gin.H{"error": "Token de autorización requerido"})
			c.Abort()
			return
		}

		// Remover "Bearer " del token
		if len(tokenString) > 7 && tokenString[:7] == "Bearer " {
			tokenString = tokenString[7:]
		}

		// Verificar token
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			return []byte(getEnv("JWT_SECRET", "heartguard-superadmin-secret-key-123")), nil
		})

		if err != nil || !token.Valid {
			c.JSON(401, gin.H{"error": "Token inválido"})
			c.Abort()
			return
		}

		// Extraer información del token
		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			usuarioID := int(claims["usuario_id"].(float64))
			rol := claims["rol"].(string)
			
			// Verificar que sea superadministrador
			if rol != "superadmin" {
				c.JSON(403, gin.H{"error": "Acceso denegado. Solo superadministradores"})
				c.Abort()
				return
			}
			
			c.Set("usuario_id", usuarioID)
			c.Set("email", claims["email"])
			c.Set("rol", rol)
		}

		c.Next()
	}
}

// =========================================================
// FUNCIONES AUXILIARES
// =========================================================

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

