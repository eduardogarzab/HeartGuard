package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/go-redis/redis/v8"
	_ "github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
)

// Estructuras de datos
type Usuario struct {
	ID           int    `json:"id"`
	FamiliaID    int    `json:"familia_id"`
	Nombre       string `json:"nombre"`
	Apellido     string `json:"apellido"`
	Email        string `json:"email"`
	Telefono     string `json:"telefono"`
	Rol          string `json:"rol"`
	Username     string `json:"username"`
	Activo       bool   `json:"activo"`
	FechaRegistro time.Time `json:"fecha_registro"`
}

type Familia struct {
	ID           int    `json:"id"`
	ColoniaID    int    `json:"colonia_id"`
	Nombre       string `json:"nombre"`
	AdminID      int    `json:"admin_id"`
	Activa       bool   `json:"activa"`
	FechaCreacion time.Time `json:"fecha_creacion"`
}

type Colonia struct {
	ID           int    `json:"id"`
	Nombre       string `json:"nombre"`
	Direccion    string `json:"direccion"`
	EncargadoID  int    `json:"encargado_id"`
	Activa       bool   `json:"activa"`
	FechaCreacion time.Time `json:"fecha_creacion"`
}

type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type LoginResponse struct {
	Token    string   `json:"token"`
	Usuario  Usuario  `json:"usuario"`
	Familia  Familia  `json:"familia"`
	Colonia  Colonia  `json:"colonia"`
}

// Variables globales
var db *sql.DB
var rdb *redis.Client

func main() {
	// Configuración de la base de datos
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbUser := getEnv("DB_USER", "heartguard")
	dbPassword := getEnv("DB_PASSWORD", "heartguard123")
	dbName := getEnv("DB_NAME", "heartguard")

	// Cadena de conexión
	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	// Conectar a la base de datos
	var err error
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal("Error conectando a la base de datos:", err)
	}
	defer db.Close()

	// Verificar la conexión
	if err = db.Ping(); err != nil {
		log.Fatal("Error verificando conexión a la base de datos:", err)
	}

	// Configurar Redis
	redisHost := getEnv("REDIS_HOST", "localhost")
	redisPort := getEnv("REDIS_PORT", "6379")
	rdb = redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%s", redisHost, redisPort),
	})

	// Verificar conexión a Redis
	_, err = rdb.Ping(rdb.Context()).Result()
	if err != nil {
		log.Fatal("Error conectando a Redis:", err)
	}

	fmt.Println("✅ Conexión a la base de datos establecida correctamente")
	fmt.Println("✅ Conexión a Redis establecida correctamente")

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

	// Rutas públicas
	r.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "HeartGuard API - Sistema de Monitoreo de Salud",
			"version": "1.0.0",
			"endpoints": gin.H{
				"login": "POST /api/v1/login",
				"colonias": "GET /api/v1/colonias",
				"familias": "GET /api/v1/familias",
				"usuarios": "GET /api/v1/usuarios",
			},
		})
	})

	// API de autenticación
	api := r.Group("/api/v1")
	{
		api.POST("/login", login)
		api.POST("/logout", logout)
		
		// Rutas protegidas
		protected := api.Group("/")
		protected.Use(authMiddleware())
		{
			// CRUD Colonias
			protected.GET("/colonias", getColonias)
			protected.POST("/colonias", createColonia)
			protected.GET("/colonias/:id", getColonia)
			protected.PUT("/colonias/:id", updateColonia)
			protected.DELETE("/colonias/:id", deleteColonia)
			
			// CRUD Familias
			protected.GET("/familias", getFamilias)
			protected.POST("/familias", createFamilia)
			protected.GET("/familias/:id", getFamilia)
			protected.PUT("/familias/:id", updateFamilia)
			protected.DELETE("/familias/:id", deleteFamilia)
			
			// CRUD Usuarios
			protected.GET("/usuarios", getUsuarios)
			protected.POST("/usuarios", createUsuario)
			protected.GET("/usuarios/:id", getUsuario)
			protected.PUT("/usuarios/:id", updateUsuario)
			protected.DELETE("/usuarios/:id", deleteUsuario)
			
			// Contactos de emergencia
			protected.GET("/usuarios/:id/contactos", getContactosEmergencia)
			protected.POST("/usuarios/:id/contactos", createContactoEmergencia)
			protected.PUT("/contactos/:id", updateContactoEmergencia)
			protected.DELETE("/contactos/:id", deleteContactoEmergencia)
			
			// Alertas
			protected.GET("/alertas", getAlertas)
			protected.GET("/usuarios/:id/alertas", getAlertasUsuario)
			protected.PUT("/alertas/:id/resolver", resolverAlerta)
		}
	}


	// Iniciar servidor
	port := getEnv("PORT", "8080")
	fmt.Printf("🚀 Servidor HeartGuard iniciado en http://localhost:%s\n", port)
	fmt.Printf("🔗 API REST: http://localhost:%s/api/v1\n", port)
	r.Run(":" + port)
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

	// Buscar usuario en la base de datos
	var usuario Usuario
	var passwordHash string
	var email, telefono sql.NullString
	query := `SELECT usuario_id, familia_id, nombre, apellido, email, telefono, rol, username, activo, fecha_registro, password_hash 
			  FROM usuarios WHERE username = $1 AND activo = true`
	
	err := db.QueryRow(query, req.Username).Scan(
		&usuario.ID, &usuario.FamiliaID, &usuario.Nombre, &usuario.Apellido,
		&email, &telefono, &usuario.Rol, &usuario.Username,
		&usuario.Activo, &usuario.FechaRegistro, &passwordHash,
	)

	// Manejar campos NULL
	if email.Valid {
		usuario.Email = email.String
	}
	if telefono.Valid {
		usuario.Telefono = telefono.String
	}

	if err != nil {
		log.Printf("Error buscando usuario %s: %v", req.Username, err)
		c.JSON(401, gin.H{"error": "Credenciales inválidas"})
		return
	}

	log.Printf("Usuario encontrado: %s, hash: %s", usuario.Username, passwordHash)

	// Verificar contraseña
	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password)); err != nil {
		log.Printf("Error verificando contraseña: %v", err)
		c.JSON(401, gin.H{"error": "Credenciales inválidas"})
		return
	}

	// Generar JWT
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"usuario_id": usuario.ID,
		"username":   usuario.Username,
		"rol":        usuario.Rol,
		"exp":        time.Now().Add(time.Hour * 24).Unix(),
	})

	tokenString, err := token.SignedString([]byte(getEnv("JWT_SECRET", "heartguard-jwt-secret-key-123")))
	if err != nil {
		c.JSON(500, gin.H{"error": "Error generando token"})
		return
	}

	// Obtener información de familia y colonia
	var familia Familia
	var colonia Colonia

	// Obtener familia
	familiaQuery := `SELECT familia_id, colonia_id, nombre, admin_id, activa, fecha_creacion 
					 FROM familias WHERE familia_id = $1`
	db.QueryRow(familiaQuery, usuario.FamiliaID).Scan(
		&familia.ID, &familia.ColoniaID, &familia.Nombre, &familia.AdminID,
		&familia.Activa, &familia.FechaCreacion,
	)

	// Obtener colonia
	coloniaQuery := `SELECT colonia_id, nombre, direccion, encargado_id, activa, fecha_creacion 
					 FROM colonias WHERE colonia_id = $1`
	db.QueryRow(coloniaQuery, familia.ColoniaID).Scan(
		&colonia.ID, &colonia.Nombre, &colonia.Direccion, &colonia.EncargadoID,
		&colonia.Activa, &colonia.FechaCreacion,
	)

	// Guardar sesión en Redis
	sessionKey := fmt.Sprintf("session:%d", usuario.ID)
	rdb.Set(rdb.Context(), sessionKey, tokenString, time.Hour*24)

	// Actualizar último acceso
	updateQuery := `UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE usuario_id = $1`
	db.Exec(updateQuery, usuario.ID)

	c.JSON(200, LoginResponse{
		Token:   tokenString,
		Usuario: usuario,
		Familia: familia,
		Colonia: colonia,
	})
}

func logout(c *gin.Context) {
	// Obtener token del header
	tokenString := c.GetHeader("Authorization")
	if tokenString == "" {
		c.JSON(400, gin.H{"error": "Token no proporcionado"})
		return
	}

	// Remover "Bearer " del token
	if len(tokenString) > 7 && tokenString[:7] == "Bearer " {
		tokenString = tokenString[7:]
	}

	// Decodificar token para obtener usuario_id
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		return []byte(getEnv("JWT_SECRET", "heartguard-jwt-secret-key-123")), nil
	})

	if err != nil {
		c.JSON(401, gin.H{"error": "Token inválido"})
		return
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		usuarioID := int(claims["usuario_id"].(float64))
		
		// Eliminar sesión de Redis
		sessionKey := fmt.Sprintf("session:%d", usuarioID)
		rdb.Del(rdb.Context(), sessionKey)
		
		c.JSON(200, gin.H{"message": "Sesión cerrada correctamente"})
	} else {
		c.JSON(401, gin.H{"error": "Token inválido"})
	}
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
			return []byte(getEnv("JWT_SECRET", "heartguard-jwt-secret-key-123")), nil
		})

		if err != nil || !token.Valid {
			c.JSON(401, gin.H{"error": "Token inválido"})
			c.Abort()
			return
		}

		// Extraer información del token
		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			c.Set("usuario_id", int(claims["usuario_id"].(float64)))
			c.Set("username", claims["username"].(string))
			c.Set("rol", claims["rol"].(string))
		}

		c.Next()
	}
}

// =========================================================
// CRUD COLONIAS
// =========================================================

func getColonias(c *gin.Context) {
	rows, err := db.Query(`SELECT colonia_id, nombre, direccion, encargado_id, activa, fecha_creacion 
						   FROM colonias ORDER BY fecha_creacion DESC`)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando colonias"})
		return
	}
	defer rows.Close()

	var colonias []Colonia
	for rows.Next() {
		var colonia Colonia
		err := rows.Scan(&colonia.ID, &colonia.Nombre, &colonia.Direccion, 
						&colonia.EncargadoID, &colonia.Activa, &colonia.FechaCreacion)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando colonias"})
			return
		}
		colonias = append(colonias, colonia)
	}

	c.JSON(200, colonias)
}

func createColonia(c *gin.Context) {
	var colonia Colonia
	if err := c.ShouldBindJSON(&colonia); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	query := `INSERT INTO colonias (nombre, direccion, encargado_id) VALUES ($1, $2, $3) RETURNING colonia_id, fecha_creacion`
	err := db.QueryRow(query, colonia.Nombre, colonia.Direccion, colonia.EncargadoID).Scan(&colonia.ID, &colonia.FechaCreacion)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error creando colonia"})
		return
	}

	colonia.Activa = true
	c.JSON(201, colonia)
}

func getColonia(c *gin.Context) {
	id := c.Param("id")
	var colonia Colonia
	
	query := `SELECT colonia_id, nombre, direccion, encargado_id, activa, fecha_creacion 
			  FROM colonias WHERE colonia_id = $1`
	err := db.QueryRow(query, id).Scan(&colonia.ID, &colonia.Nombre, &colonia.Direccion, 
									  &colonia.EncargadoID, &colonia.Activa, &colonia.FechaCreacion)
	if err != nil {
		c.JSON(404, gin.H{"error": "Colonia no encontrada"})
		return
	}

	c.JSON(200, colonia)
}

func updateColonia(c *gin.Context) {
	id := c.Param("id")
	var colonia Colonia
	if err := c.ShouldBindJSON(&colonia); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	query := `UPDATE colonias SET nombre = $1, direccion = $2, encargado_id = $3, activa = $4 
			  WHERE colonia_id = $5 RETURNING fecha_creacion`
	err := db.QueryRow(query, colonia.Nombre, colonia.Direccion, colonia.EncargadoID, 
					  colonia.Activa, id).Scan(&colonia.FechaCreacion)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error actualizando colonia"})
		return
	}

	colonia.ID, _ = strconv.Atoi(id)
	c.JSON(200, colonia)
}

func deleteColonia(c *gin.Context) {
	id := c.Param("id")
	
	query := `UPDATE colonias SET activa = false WHERE colonia_id = $1`
	result, err := db.Exec(query, id)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error eliminando colonia"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Colonia no encontrada"})
		return
	}

	c.JSON(200, gin.H{"message": "Colonia eliminada correctamente"})
}

// =========================================================
// CRUD FAMILIAS
// =========================================================

func getFamilias(c *gin.Context) {
	rows, err := db.Query(`SELECT familia_id, colonia_id, nombre, admin_id, activa, fecha_creacion 
						   FROM familias ORDER BY fecha_creacion DESC`)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando familias"})
		return
	}
	defer rows.Close()

	var familias []Familia
	for rows.Next() {
		var familia Familia
		err := rows.Scan(&familia.ID, &familia.ColoniaID, &familia.Nombre, 
						&familia.AdminID, &familia.Activa, &familia.FechaCreacion)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando familias"})
			return
		}
		familias = append(familias, familia)
	}

	c.JSON(200, familias)
}

func createFamilia(c *gin.Context) {
	var familia Familia
	if err := c.ShouldBindJSON(&familia); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	query := `INSERT INTO familias (colonia_id, nombre, admin_id) VALUES ($1, $2, $3) RETURNING familia_id, fecha_creacion`
	err := db.QueryRow(query, familia.ColoniaID, familia.Nombre, familia.AdminID).Scan(&familia.ID, &familia.FechaCreacion)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error creando familia"})
		return
	}

	familia.Activa = true
	c.JSON(201, familia)
}

func getFamilia(c *gin.Context) {
	id := c.Param("id")
	var familia Familia
	
	query := `SELECT familia_id, colonia_id, nombre, admin_id, activa, fecha_creacion 
			  FROM familias WHERE familia_id = $1`
	err := db.QueryRow(query, id).Scan(&familia.ID, &familia.ColoniaID, &familia.Nombre, 
									  &familia.AdminID, &familia.Activa, &familia.FechaCreacion)
	if err != nil {
		c.JSON(404, gin.H{"error": "Familia no encontrada"})
		return
	}

	c.JSON(200, familia)
}

func updateFamilia(c *gin.Context) {
	id := c.Param("id")
	var familia Familia
	if err := c.ShouldBindJSON(&familia); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	query := `UPDATE familias SET colonia_id = $1, nombre = $2, admin_id = $3, activa = $4 
			  WHERE familia_id = $5 RETURNING fecha_creacion`
	err := db.QueryRow(query, familia.ColoniaID, familia.Nombre, familia.AdminID, 
					  familia.Activa, id).Scan(&familia.FechaCreacion)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error actualizando familia"})
		return
	}

	familia.ID, _ = strconv.Atoi(id)
	c.JSON(200, familia)
}

func deleteFamilia(c *gin.Context) {
	id := c.Param("id")
	
	query := `UPDATE familias SET activa = false WHERE familia_id = $1`
	result, err := db.Exec(query, id)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error eliminando familia"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Familia no encontrada"})
		return
	}

	c.JSON(200, gin.H{"message": "Familia eliminada correctamente"})
}

// =========================================================
// CRUD USUARIOS
// =========================================================

func getUsuarios(c *gin.Context) {
	rows, err := db.Query(`SELECT usuario_id, familia_id, nombre, apellido, email, telefono, rol, username, activo, fecha_registro 
						   FROM usuarios ORDER BY fecha_registro DESC`)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando usuarios"})
		return
	}
	defer rows.Close()

	var usuarios []Usuario
	for rows.Next() {
		var usuario Usuario
		var email, telefono sql.NullString
		err := rows.Scan(&usuario.ID, &usuario.FamiliaID, &usuario.Nombre, &usuario.Apellido,
						&email, &telefono, &usuario.Rol, &usuario.Username,
						&usuario.Activo, &usuario.FechaRegistro)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando usuarios"})
			return
		}
		
		// Manejar campos NULL
		if email.Valid {
			usuario.Email = email.String
		}
		if telefono.Valid {
			usuario.Telefono = telefono.String
		}
		
		usuarios = append(usuarios, usuario)
	}

	c.JSON(200, usuarios)
}

func createUsuario(c *gin.Context) {
	var usuario Usuario
	
	// Estructura para recibir datos del request
	type CreateUsuarioRequest struct {
		FamiliaID       int    `json:"familia_id" binding:"required"`
		Nombre          string `json:"nombre" binding:"required"`
		Apellido        string `json:"apellido"`
		Email           string `json:"email"`
		Telefono        string `json:"telefono"`
		Rol             string `json:"rol" binding:"required"`
		Username        string `json:"username" binding:"required"`
		Password        string `json:"password" binding:"required"`
		FechaNacimiento string `json:"fecha_nacimiento"`
	}

	var req CreateUsuarioRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Encriptar contraseña
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error encriptando contraseña"})
		return
	}

	query := `INSERT INTO usuarios (familia_id, nombre, apellido, email, telefono, rol, username, password_hash, activo) 
			  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING usuario_id, fecha_registro`
	
	// Manejar campos opcionales
	var email, telefono interface{}
	if req.Email != "" {
		email = req.Email
	} else {
		email = nil
	}
	if req.Telefono != "" {
		telefono = req.Telefono
	} else {
		telefono = nil
	}
	
	err = db.QueryRow(query, req.FamiliaID, req.Nombre, req.Apellido, email, telefono, 
					 req.Rol, req.Username, string(hashedPassword), true).Scan(&usuario.ID, &usuario.FechaRegistro)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error creando usuario"})
		return
	}

	usuario.FamiliaID = req.FamiliaID
	usuario.Nombre = req.Nombre
	usuario.Apellido = req.Apellido
	usuario.Email = req.Email
	usuario.Telefono = req.Telefono
	usuario.Rol = req.Rol
	usuario.Username = req.Username
	usuario.Activo = true

	c.JSON(201, usuario)
}

func getUsuario(c *gin.Context) {
	id := c.Param("id")
	var usuario Usuario
	
	query := `SELECT usuario_id, familia_id, nombre, apellido, email, telefono, rol, username, activo, fecha_registro 
			  FROM usuarios WHERE usuario_id = $1`
	err := db.QueryRow(query, id).Scan(&usuario.ID, &usuario.FamiliaID, &usuario.Nombre, &usuario.Apellido,
									  &usuario.Email, &usuario.Telefono, &usuario.Rol, &usuario.Username,
									  &usuario.Activo, &usuario.FechaRegistro)
	if err != nil {
		c.JSON(404, gin.H{"error": "Usuario no encontrado"})
		return
	}

	c.JSON(200, usuario)
}

func updateUsuario(c *gin.Context) {
	id := c.Param("id")
	
	// Estructura para recibir datos del request
	type UpdateUsuarioRequest struct {
		FamiliaID       int    `json:"familia_id"`
		Nombre          string `json:"nombre"`
		Apellido        string `json:"apellido"`
		Email           string `json:"email"`
		Telefono        string `json:"telefono"`
		Rol             string `json:"rol"`
		Username        string `json:"username"`
		Password        string `json:"password"`
		FechaNacimiento string `json:"fecha_nacimiento"`
		Activo          bool   `json:"activo"`
	}

	var req UpdateUsuarioRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Construir query dinámicamente
	setParts := []string{}
	args := []interface{}{}
	argIndex := 1

	if req.FamiliaID != 0 {
		setParts = append(setParts, fmt.Sprintf("familia_id = $%d", argIndex))
		args = append(args, req.FamiliaID)
		argIndex++
	}
	if req.Nombre != "" {
		setParts = append(setParts, fmt.Sprintf("nombre = $%d", argIndex))
		args = append(args, req.Nombre)
		argIndex++
	}
	if req.Apellido != "" {
		setParts = append(setParts, fmt.Sprintf("apellido = $%d", argIndex))
		args = append(args, req.Apellido)
		argIndex++
	}
	if req.Email != "" {
		setParts = append(setParts, fmt.Sprintf("email = $%d", argIndex))
		args = append(args, req.Email)
		argIndex++
	}
	if req.Telefono != "" {
		setParts = append(setParts, fmt.Sprintf("telefono = $%d", argIndex))
		args = append(args, req.Telefono)
		argIndex++
	}
	if req.Rol != "" {
		setParts = append(setParts, fmt.Sprintf("rol = $%d", argIndex))
		args = append(args, req.Rol)
		argIndex++
	}
	if req.Username != "" {
		setParts = append(setParts, fmt.Sprintf("username = $%d", argIndex))
		args = append(args, req.Username)
		argIndex++
	}
	if req.Password != "" {
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error encriptando contraseña"})
			return
		}
		setParts = append(setParts, fmt.Sprintf("password_hash = $%d", argIndex))
		args = append(args, string(hashedPassword))
		argIndex++
	}
	if req.FechaNacimiento != "" {
		setParts = append(setParts, fmt.Sprintf("fecha_nacimiento = $%d", argIndex))
		args = append(args, req.FechaNacimiento)
		argIndex++
	}
	
	setParts = append(setParts, fmt.Sprintf("activo = $%d", argIndex))
	args = append(args, req.Activo)
	argIndex++

	args = append(args, id) // ID para WHERE

	query := fmt.Sprintf("UPDATE usuarios SET %s WHERE usuario_id = $%d", 
						strings.Join(setParts, ", "), argIndex)
	
	result, err := db.Exec(query, args...)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error actualizando usuario"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Usuario no encontrado"})
		return
	}

	c.JSON(200, gin.H{"message": "Usuario actualizado correctamente"})
}

func deleteUsuario(c *gin.Context) {
	id := c.Param("id")
	
	query := `UPDATE usuarios SET activo = false WHERE usuario_id = $1`
	result, err := db.Exec(query, id)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error eliminando usuario"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Usuario no encontrado"})
		return
	}

	c.JSON(200, gin.H{"message": "Usuario eliminado correctamente"})
}

// =========================================================
// CONTACTOS DE EMERGENCIA
// =========================================================

func getContactosEmergencia(c *gin.Context) {
	usuarioID := c.Param("id")
	
	rows, err := db.Query(`SELECT contacto_id, usuario_id, nombre, relacion, telefono, email, es_principal, fecha_creacion 
						   FROM contactos_emergencia WHERE usuario_id = $1 ORDER BY es_principal DESC, fecha_creacion DESC`, usuarioID)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando contactos"})
		return
	}
	defer rows.Close()

	var contactos []map[string]interface{}
	for rows.Next() {
		var contacto map[string]interface{} = make(map[string]interface{})
		var contactoID, usuarioID int
		var nombre, relacion, telefono, email string
		var esPrincipal bool
		var fechaCreacion time.Time
		
		err := rows.Scan(&contactoID, &usuarioID, &nombre, &relacion, &telefono, &email, &esPrincipal, &fechaCreacion)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando contactos"})
			return
		}
		
		contacto["contacto_id"] = contactoID
		contacto["usuario_id"] = usuarioID
		contacto["nombre"] = nombre
		contacto["relacion"] = relacion
		contacto["telefono"] = telefono
		contacto["email"] = email
		contacto["es_principal"] = esPrincipal
		contacto["fecha_creacion"] = fechaCreacion
		
		contactos = append(contactos, contacto)
	}

	c.JSON(200, contactos)
}

func createContactoEmergencia(c *gin.Context) {
	usuarioID := c.Param("id")
	
	type CreateContactoRequest struct {
		Nombre       string `json:"nombre" binding:"required"`
		Relacion     string `json:"relacion"`
		Telefono     string `json:"telefono" binding:"required"`
		Email        string `json:"email"`
		EsPrincipal  bool   `json:"es_principal"`
	}

	var req CreateContactoRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	query := `INSERT INTO contactos_emergencia (usuario_id, nombre, relacion, telefono, email, es_principal) 
			  VALUES ($1, $2, $3, $4, $5, $6) RETURNING contacto_id, fecha_creacion`
	
	var contactoID int
	var fechaCreacion time.Time
	err := db.QueryRow(query, usuarioID, req.Nombre, req.Relacion, req.Telefono, req.Email, req.EsPrincipal).Scan(&contactoID, &fechaCreacion)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error creando contacto"})
		return
	}

	contacto := map[string]interface{}{
		"contacto_id":     contactoID,
		"usuario_id":      usuarioID,
		"nombre":          req.Nombre,
		"relacion":        req.Relacion,
		"telefono":        req.Telefono,
		"email":           req.Email,
		"es_principal":    req.EsPrincipal,
		"fecha_creacion":  fechaCreacion,
	}

	c.JSON(201, contacto)
}

func updateContactoEmergencia(c *gin.Context) {
	contactoID := c.Param("id")
	
	type UpdateContactoRequest struct {
		Nombre      string `json:"nombre"`
		Relacion    string `json:"relacion"`
		Telefono    string `json:"telefono"`
		Email       string `json:"email"`
		EsPrincipal bool   `json:"es_principal"`
	}

	var req UpdateContactoRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	query := `UPDATE contactos_emergencia SET nombre = $1, relacion = $2, telefono = $3, email = $4, es_principal = $5 
			  WHERE contacto_id = $6`
	
	result, err := db.Exec(query, req.Nombre, req.Relacion, req.Telefono, req.Email, req.EsPrincipal, contactoID)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error actualizando contacto"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Contacto no encontrado"})
		return
	}

	c.JSON(200, gin.H{"message": "Contacto actualizado correctamente"})
}

func deleteContactoEmergencia(c *gin.Context) {
	contactoID := c.Param("id")
	
	query := `DELETE FROM contactos_emergencia WHERE contacto_id = $1`
	result, err := db.Exec(query, contactoID)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error eliminando contacto"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Contacto no encontrado"})
		return
	}

	c.JSON(200, gin.H{"message": "Contacto eliminado correctamente"})
}

// =========================================================
// ALERTAS
// =========================================================

func getAlertas(c *gin.Context) {
	rows, err := db.Query(`SELECT a.alerta_id, a.usuario_id, a.tipo, a.nivel, a.mensaje, a.datos_adicionales, 
						   a.resuelta, a.fecha_creacion, a.fecha_resolucion, u.nombre as usuario_nombre
						   FROM alertas a 
						   JOIN usuarios u ON a.usuario_id = u.usuario_id 
						   ORDER BY a.fecha_creacion DESC`)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando alertas"})
		return
	}
	defer rows.Close()

	var alertas []map[string]interface{}
	for rows.Next() {
		var alerta map[string]interface{} = make(map[string]interface{})
		var alertaID, usuarioID int
		var tipo, nivel, mensaje, usuarioNombre string
		var datosAdicionales []byte
		var resuelta bool
		var fechaCreacion time.Time
		var fechaResolucion *time.Time
		
		err := rows.Scan(&alertaID, &usuarioID, &tipo, &nivel, &mensaje, &datosAdicionales, 
						&resuelta, &fechaCreacion, &fechaResolucion, &usuarioNombre)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando alertas"})
			return
		}
		
		alerta["alerta_id"] = alertaID
		alerta["usuario_id"] = usuarioID
		alerta["tipo"] = tipo
		alerta["nivel"] = nivel
		alerta["mensaje"] = mensaje
		alerta["datos_adicionales"] = string(datosAdicionales)
		alerta["resuelta"] = resuelta
		alerta["fecha_creacion"] = fechaCreacion
		alerta["fecha_resolucion"] = fechaResolucion
		alerta["usuario_nombre"] = usuarioNombre
		
		alertas = append(alertas, alerta)
	}

	c.JSON(200, alertas)
}

func getAlertasUsuario(c *gin.Context) {
	usuarioID := c.Param("id")
	
	rows, err := db.Query(`SELECT alerta_id, usuario_id, tipo, nivel, mensaje, datos_adicionales, 
						   resuelta, fecha_creacion, fecha_resolucion
						   FROM alertas WHERE usuario_id = $1 ORDER BY fecha_creacion DESC`, usuarioID)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando alertas del usuario"})
		return
	}
	defer rows.Close()

	var alertas []map[string]interface{}
	for rows.Next() {
		var alerta map[string]interface{} = make(map[string]interface{})
		var alertaID, usuarioID int
		var tipo, nivel, mensaje string
		var datosAdicionales []byte
		var resuelta bool
		var fechaCreacion time.Time
		var fechaResolucion *time.Time
		
		err := rows.Scan(&alertaID, &usuarioID, &tipo, &nivel, &mensaje, &datosAdicionales, 
						&resuelta, &fechaCreacion, &fechaResolucion)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando alertas"})
			return
		}
		
		alerta["alerta_id"] = alertaID
		alerta["usuario_id"] = usuarioID
		alerta["tipo"] = tipo
		alerta["nivel"] = nivel
		alerta["mensaje"] = mensaje
		alerta["datos_adicionales"] = string(datosAdicionales)
		alerta["resuelta"] = resuelta
		alerta["fecha_creacion"] = fechaCreacion
		alerta["fecha_resolucion"] = fechaResolucion
		
		alertas = append(alertas, alerta)
	}

	c.JSON(200, alertas)
}

func resolverAlerta(c *gin.Context) {
	alertaID := c.Param("id")
	
	query := `UPDATE alertas SET resuelta = true, fecha_resolucion = CURRENT_TIMESTAMP WHERE alerta_id = $1`
	result, err := db.Exec(query, alertaID)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error resolviendo alerta"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Alerta no encontrada"})
		return
	}

	c.JSON(200, gin.H{"message": "Alerta resuelta correctamente"})
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
