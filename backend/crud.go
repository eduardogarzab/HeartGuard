package main

import (
	"database/sql"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

// =========================================================
// CRUD USUARIOS - VERSIÓN NORMALIZADA
// =========================================================

func getUsuarios(c *gin.Context) {
	fmt.Println("🔍 getUsuarios called")
	
	// Usar stored procedure para obtener usuarios
	query := `SELECT * FROM sp_get_usuarios($1, $2, $3, $4, $5)`
	
	limit := c.DefaultQuery("limite", "50")
	offset := c.DefaultQuery("offset", "0")
	rolID := c.Query("rol_id")
	familiaID := c.Query("familia_id")
	activo := c.Query("activo")
	
	limitInt, _ := strconv.Atoi(limit)
	offsetInt, _ := strconv.Atoi(offset)
	
	var rolIDInt *int
	var familiaIDInt *int
	var activoBool *bool
	
	if rolID != "" {
		if id, err := strconv.Atoi(rolID); err == nil {
			rolIDInt = &id
		}
	}
	
	if familiaID != "" {
		if id, err := strconv.Atoi(familiaID); err == nil {
			familiaIDInt = &id
		}
	}
	
	if activo != "" {
		if b, err := strconv.ParseBool(activo); err == nil {
			activoBool = &b
		}
	}
	
	rows, err := db.Query(query, limitInt, offsetInt, rolIDInt, familiaIDInt, activoBool)
	if err != nil {
		fmt.Printf("❌ Error querying usuarios: %v\n", err)
		c.JSON(500, gin.H{"error": "Error consultando usuarios", "details": err.Error()})
		return
	}
	defer rows.Close()

	var usuarios []map[string]interface{}
	for rows.Next() {
		var u struct {
			ID                int       `json:"id"`
			Nombre            string    `json:"nombre"`
			Email             string    `json:"email"`
			RolNombre         string    `json:"rol_nombre"`
			FamiliaNombre     string    `json:"familia_nombre"`
			Relacion          *string   `json:"relacion"`
			EsAdminFamilia    *bool     `json:"es_admin_familia"`
			UltimaActualizacion *time.Time `json:"ultima_actualizacion"`
			FechaCreacion     time.Time `json:"fecha_creacion"`
			Estado            bool      `json:"estado"`
		}

		err := rows.Scan(&u.ID, &u.Nombre, &u.Email, &u.RolNombre, &u.FamiliaNombre, 
			&u.Relacion, &u.EsAdminFamilia, &u.UltimaActualizacion, &u.FechaCreacion, &u.Estado)
		if err != nil {
			fmt.Printf("❌ Error scanning usuario: %v\n", err)
			continue
		}

		usuarios = append(usuarios, map[string]interface{}{
			"id":                u.ID,
			"nombre":            u.Nombre,
			"email":             u.Email,
			"rol":               u.RolNombre,
			"familia_nombre":    u.FamiliaNombre,
			"relacion":          u.Relacion,
			"es_admin_familia":  u.EsAdminFamilia,
			"ultima_actualizacion": u.UltimaActualizacion,
			"fecha_creacion":    u.FechaCreacion,
			"estado":            u.Estado,
		})
	}

	fmt.Printf("✅ Found %d usuarios\n", len(usuarios))
	c.JSON(200, gin.H{
		"success": true,
		"data":    usuarios,
		"total":   len(usuarios),
	})
}

func createUsuario(c *gin.Context) {
	fmt.Println("🔍 createUsuario called")
	
	var req struct {
		Nombre    string `json:"nombre" binding:"required"`
		Email     string `json:"email" binding:"required,email"`
		Password  string `json:"password" binding:"required,min=6"`
		Rol       string `json:"rol" binding:"required"`
		FamiliaID *int   `json:"familia_id"`
		Relacion  string `json:"relacion"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("❌ Error binding request: %v\n", err)
		c.JSON(400, gin.H{"error": "Datos inválidos", "details": err.Error()})
		return
	}

	// Verificar si el email ya existe
	var existingID int
	err := db.QueryRow("SELECT id FROM usuarios WHERE email = $1", req.Email).Scan(&existingID)
	if err == nil {
		c.JSON(400, gin.H{"error": "El email ya está registrado"})
		return
	}

	// Obtener ID del rol
	var rolID int
	err = db.QueryRow("SELECT id FROM roles WHERE nombre = $1", req.Rol).Scan(&rolID)
	if err != nil {
		c.JSON(400, gin.H{"error": "Rol inválido"})
		return
	}

	// Hash de la contraseña
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		fmt.Printf("❌ Error hashing password: %v\n", err)
		c.JSON(500, gin.H{"error": "Error procesando contraseña"})
		return
	}

	// Insertar usuario
	query := `
		INSERT INTO usuarios (nombre, email, password_hash, rol_id, fecha_creacion)
		VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
		RETURNING id, nombre, email, rol_id, estado, fecha_creacion
	`
	
	var u struct {
		ID            int       `json:"id"`
		Nombre        string    `json:"nombre"`
		Email         string    `json:"email"`
		RolID         int       `json:"rol_id"`
		Estado        bool      `json:"estado"`
		FechaCreacion time.Time `json:"fecha_creacion"`
	}

	err = db.QueryRow(query, req.Nombre, req.Email, string(hashedPassword), rolID).
		Scan(&u.ID, &u.Nombre, &u.Email, &u.RolID, &u.Estado, &u.FechaCreacion)
	
	if err != nil {
		fmt.Printf("❌ Error inserting usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error creando usuario", "details": err.Error()})
		return
	}

	// Si se especificó familia, agregar como miembro
	if req.FamiliaID != nil {
		insertMiembroQuery := `
			INSERT INTO miembros_familia (familia_id, usuario_id, relacion, es_admin_familia, fecha_ingreso)
			VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
		`
		
		esAdminFamilia := req.Rol == "admin_familia"
		_, err = db.Exec(insertMiembroQuery, *req.FamiliaID, u.ID, req.Relacion, esAdminFamilia)
		if err != nil {
			fmt.Printf("❌ Error adding user to family: %v\n", err)
			// No fallar la operación principal, solo log
		}
	}

	fmt.Printf("✅ Usuario created with ID: %d\n", u.ID)
	c.JSON(201, gin.H{
		"success": true,
		"message": "Usuario creado exitosamente",
		"data":    u,
	})
}

func getUsuario(c *gin.Context) {
	fmt.Println("🔍 getUsuario called")
	
	id := c.Param("id")
	usuarioID, err := strconv.Atoi(id)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID inválido"})
		return
	}

	query := `
		SELECT 
			u.id, u.nombre, u.email, u.latitud, u.longitud, 
			u.estado, u.fecha_creacion, u.ultima_actualizacion,
			r.nombre as rol_nombre,
			COALESCE(f.nombre_familia, 'Sin familia') as familia_nombre,
			mf.familia_id,
			mf.relacion, mf.es_admin_familia
		FROM usuarios u
		JOIN roles r ON u.rol_id = r.id
		LEFT JOIN miembros_familia mf ON u.id = mf.usuario_id AND mf.activo = true
		LEFT JOIN familias f ON mf.familia_id = f.id AND f.estado = true
		WHERE u.id = $1
	`
	
	var u struct {
		ID                int       `json:"id"`
		Nombre            string    `json:"nombre"`
		Email             string    `json:"email"`
		Latitud           *float64  `json:"latitud"`
		Longitud          *float64  `json:"longitud"`
		Estado            bool      `json:"estado"`
		FechaCreacion     time.Time `json:"fecha_creacion"`
		UltimaActualizacion *time.Time `json:"ultima_actualizacion"`
		RolNombre         string    `json:"rol_nombre"`
		FamiliaNombre     string    `json:"familia_nombre"`
		FamiliaID         *int      `json:"familia_id"`
		Relacion          *string   `json:"relacion"`
		EsAdminFamilia    *bool     `json:"es_admin_familia"`
	}

	err = db.QueryRow(query, usuarioID).Scan(
		&u.ID, &u.Nombre, &u.Email, &u.Latitud, &u.Longitud, 
		&u.Estado, &u.FechaCreacion, &u.UltimaActualizacion,
		&u.RolNombre, &u.FamiliaNombre, &u.FamiliaID, &u.Relacion, &u.EsAdminFamilia,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(404, gin.H{"error": "Usuario no encontrado"})
		} else {
			fmt.Printf("❌ Error querying usuario: %v\n", err)
			c.JSON(500, gin.H{"error": "Error consultando usuario"})
		}
		return
	}

	fmt.Printf("✅ Usuario found: %s\n", u.Nombre)
	c.JSON(200, gin.H{
		"success": true,
		"data":    u,
	})
}

func updateUsuario(c *gin.Context) {
	fmt.Println("🔍 updateUsuario called")
	
	id := c.Param("id")
	usuarioID, err := strconv.Atoi(id)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID inválido"})
		return
	}

	var req struct {
		Nombre    *string `json:"nombre"`
		Email     *string `json:"email"`
		Rol       *string `json:"rol"`
		FamiliaID *int    `json:"familia_id"`
		Relacion  *string `json:"relacion"`
		Estado    *bool   `json:"estado"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Construir query dinámicamente
	setParts := []string{}
	args := []interface{}{}
	argIndex := 1

	if req.Nombre != nil {
		setParts = append(setParts, fmt.Sprintf("nombre = $%d", argIndex))
		args = append(args, *req.Nombre)
		argIndex++
	}
	if req.Email != nil {
		setParts = append(setParts, fmt.Sprintf("email = $%d", argIndex))
		args = append(args, *req.Email)
		argIndex++
	}
	if req.Rol != nil {
		// Obtener rol_id
		var rolID int
		err = db.QueryRow("SELECT id FROM roles WHERE nombre = $1", *req.Rol).Scan(&rolID)
		if err != nil {
			c.JSON(400, gin.H{"error": "Rol inválido"})
			return
		}
		setParts = append(setParts, fmt.Sprintf("rol_id = $%d", argIndex))
		args = append(args, rolID)
		argIndex++
	}
	if req.Estado != nil {
		setParts = append(setParts, fmt.Sprintf("estado = $%d", argIndex))
		args = append(args, *req.Estado)
		argIndex++
	}

	if len(setParts) == 0 {
		c.JSON(400, gin.H{"error": "No hay campos para actualizar"})
		return
	}

	setParts = append(setParts, "ultima_actualizacion = CURRENT_TIMESTAMP")
	args = append(args, usuarioID)

	query := fmt.Sprintf("UPDATE usuarios SET %s WHERE id = $%d RETURNING id, nombre, email, rol_id, estado, ultima_actualizacion",
		strings.Join(setParts, ", "), len(args))

	var u struct {
		ID                 int       `json:"id"`
		Nombre             string    `json:"nombre"`
		Email              string    `json:"email"`
		RolID              int       `json:"rol_id"`
		Estado             bool      `json:"estado"`
		UltimaActualizacion time.Time `json:"ultima_actualizacion"`
	}

	err = db.QueryRow(query, args...).Scan(&u.ID, &u.Nombre, &u.Email, &u.RolID, &u.Estado, &u.UltimaActualizacion)
	if err != nil {
		fmt.Printf("❌ Error updating usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error actualizando usuario"})
		return
	}

	// Actualizar membresía familiar si se especificó
	if req.FamiliaID != nil || req.Relacion != nil {
		if req.FamiliaID != nil {
			// Actualizar o crear membresía
			updateMiembroQuery := `
				INSERT INTO miembros_familia (familia_id, usuario_id, relacion, fecha_ingreso)
				VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
				ON CONFLICT (familia_id, usuario_id) 
				DO UPDATE SET relacion = EXCLUDED.relacion, activo = true
			`
			_, err = db.Exec(updateMiembroQuery, *req.FamiliaID, usuarioID, req.Relacion)
			if err != nil {
				fmt.Printf("❌ Error updating family membership: %v\n", err)
			}
		}
	}

	fmt.Printf("✅ Usuario updated: %s\n", u.Nombre)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Usuario actualizado exitosamente",
		"data":    u,
	})
}

func deleteUsuario(c *gin.Context) {
	fmt.Println("🔍 deleteUsuario called")
	
	id := c.Param("id")
	usuarioID, err := strconv.Atoi(id)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID inválido"})
		return
	}

	// Verificar si es el superusuario
	var rolNombre string
	err = db.QueryRow(`
		SELECT r.nombre 
		FROM usuarios u 
		JOIN roles r ON u.rol_id = r.id 
		WHERE u.id = $1
	`, usuarioID).Scan(&rolNombre)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(404, gin.H{"error": "Usuario no encontrado"})
		} else {
			c.JSON(500, gin.H{"error": "Error verificando usuario"})
		}
		return
	}

	if rolNombre == "superadmin" {
		c.JSON(403, gin.H{"error": "No se puede eliminar el superadministrador del sistema"})
		return
	}


	// Eliminar usuario (soft delete - cambiar estado)
	_, err = db.Exec("UPDATE usuarios SET estado = false WHERE id = $1", usuarioID)
	if err != nil {
		fmt.Printf("❌ Error deleting usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error eliminando usuario"})
		return
	}

	// Desactivar membresías familiares
	_, err = db.Exec("UPDATE miembros_familia SET activo = false WHERE usuario_id = $1", usuarioID)
	if err != nil {
		fmt.Printf("❌ Error deactivating family memberships: %v\n", err)
	}

	fmt.Printf("✅ Usuario deleted: ID %d (%s)\n", usuarioID, rolNombre)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Usuario eliminado exitosamente",
	})
}

// =========================================================
// CRUD FAMILIAS - VERSIÓN NORMALIZADA
// =========================================================

func getFamilias(c *gin.Context) {
	fmt.Println("🔍 getFamilias called")
	
	// Usar stored procedure para obtener familias
	query := `SELECT * FROM sp_get_familias($1, $2, $3)`
	
	limit := c.DefaultQuery("limite", "50")
	offset := c.DefaultQuery("offset", "0")
	activo := c.Query("activo")
	
	limitInt, _ := strconv.Atoi(limit)
	offsetInt, _ := strconv.Atoi(offset)
	
	var activoBool *bool
	if activo != "" {
		if b, err := strconv.ParseBool(activo); err == nil {
			activoBool = &b
		}
	}
	
	rows, err := db.Query(query, limitInt, offsetInt, activoBool)
	if err != nil {
		fmt.Printf("❌ Error querying familias: %v\n", err)
		c.JSON(500, gin.H{"error": "Error consultando familias", "details": err.Error()})
		return
	}
	defer rows.Close()

	var familias []map[string]interface{}
	for rows.Next() {
		var f struct {
			ID            int       `json:"id"`
			NombreFamilia string    `json:"nombre_familia"`
			CodigoFamilia *string   `json:"codigo_familia"`
			FechaCreacion time.Time `json:"fecha_creacion"`
			Estado        bool      `json:"estado"`
			TotalMiembros int64     `json:"total_miembros"`
			TotalAdmins   int64     `json:"total_admins"`
		}

		err := rows.Scan(&f.ID, &f.NombreFamilia, &f.CodigoFamilia, &f.FechaCreacion, &f.Estado, &f.TotalMiembros, &f.TotalAdmins)
		if err != nil {
			fmt.Printf("❌ Error scanning familia: %v\n", err)
			continue
		}

		familias = append(familias, map[string]interface{}{
			"id":              f.ID,
			"nombre_familia":  f.NombreFamilia,
			"codigo_familia":  f.CodigoFamilia,
			"fecha_creacion":  f.FechaCreacion,
			"estado":          f.Estado,
			"total_miembros":  f.TotalMiembros,
			"total_admins":    f.TotalAdmins,
		})
	}

	fmt.Printf("✅ Found %d familias\n", len(familias))
	c.JSON(200, gin.H{
		"success": true,
		"data":    familias,
		"total":   len(familias),
	})
}

func createFamilia(c *gin.Context) {
	fmt.Println("🔍 createFamilia called")
	
	var req struct {
		NombreFamilia string `json:"nombre_familia" binding:"required"`
		CodigoFamilia string `json:"codigo_familia"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("❌ Error binding request: %v\n", err)
		c.JSON(400, gin.H{"error": "Datos inválidos", "details": err.Error()})
		return
	}

	// Usar stored procedure para crear familia
	var codigoFamilia *string
	if req.CodigoFamilia != "" {
		codigoFamilia = &req.CodigoFamilia
	}

	rows, err := db.Query(`SELECT * FROM sp_create_familia($1, $2)`, req.NombreFamilia, codigoFamilia)
	if err != nil {
		fmt.Printf("❌ Error creating familia: %v\n", err)
		c.JSON(500, gin.H{"error": "Error creando familia", "details": err.Error()})
		return
	}
	defer rows.Close()

	var f struct {
		ID            int       `json:"id"`
		NombreFamilia string    `json:"nombre_familia"`
		CodigoFamilia *string   `json:"codigo_familia"`
		FechaCreacion time.Time `json:"fecha_creacion"`
	}

	if rows.Next() {
		err = rows.Scan(&f.ID, &f.NombreFamilia, &f.CodigoFamilia, &f.FechaCreacion)
		if err != nil {
			fmt.Printf("❌ Error scanning familia created: %v\n", err)
			c.JSON(500, gin.H{"error": "Error obteniendo datos de la familia creada"})
			return
		}
	}

	fmt.Printf("✅ Familia created with ID: %d\n", f.ID)
	c.JSON(201, gin.H{
		"success": true,
		"message": "Familia creada exitosamente",
		"data":    f,
	})
}

func getFamilia(c *gin.Context) {
	fmt.Println("🔍 getFamilia called")
	
	id := c.Param("id")
	familiaID, err := strconv.Atoi(id)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID inválido"})
		return
	}

	query := `
		SELECT 
			f.id, f.nombre_familia, f.codigo_familia, f.fecha_creacion, f.estado,
			COUNT(mf.usuario_id) as total_miembros,
			COUNT(CASE WHEN mf.es_admin_familia = true THEN 1 END) as total_admins
		FROM familias f
		LEFT JOIN miembros_familia mf ON f.id = mf.familia_id AND mf.activo = true
		WHERE f.id = $1
		GROUP BY f.id, f.nombre_familia, f.codigo_familia, f.fecha_creacion, f.estado
	`
	
	var f struct {
		ID            int       `json:"id"`
		NombreFamilia string    `json:"nombre_familia"`
		CodigoFamilia *string   `json:"codigo_familia"`
		FechaCreacion time.Time `json:"fecha_creacion"`
		Estado        bool      `json:"estado"`
		TotalMiembros int       `json:"total_miembros"`
		TotalAdmins   int       `json:"total_admins"`
	}

	err = db.QueryRow(query, familiaID).Scan(&f.ID, &f.NombreFamilia, &f.CodigoFamilia, &f.FechaCreacion, &f.Estado, &f.TotalMiembros, &f.TotalAdmins)
	
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(404, gin.H{"error": "Familia no encontrada"})
		} else {
			fmt.Printf("❌ Error querying familia: %v\n", err)
			c.JSON(500, gin.H{"error": "Error consultando familia"})
		}
		return
	}

	fmt.Printf("✅ Familia found: %s\n", f.NombreFamilia)
	c.JSON(200, gin.H{
		"success": true,
		"data":    f,
	})
}

func updateFamilia(c *gin.Context) {
	fmt.Println("🔍 updateFamilia called")
	
	id := c.Param("id")
	familiaID, err := strconv.Atoi(id)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID inválido"})
		return
	}

	var req struct {
		NombreFamilia *string `json:"nombre_familia"`
		CodigoFamilia *string `json:"codigo_familia"`
		Estado        *bool   `json:"estado"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Usar stored procedure para actualizar familia
	rows, err := db.Query(`SELECT sp_update_familia($1, $2, $3, $4)`, 
		familiaID, req.NombreFamilia, req.CodigoFamilia, req.Estado)
	if err != nil {
		fmt.Printf("❌ Error updating familia: %v\n", err)
		c.JSON(500, gin.H{"error": "Error actualizando familia"})
		return
	}
	defer rows.Close()

	var success bool
	if rows.Next() {
		err = rows.Scan(&success)
		if err != nil || !success {
			c.JSON(404, gin.H{"error": "Familia no encontrada"})
			return
		}
	}

	fmt.Printf("✅ Familia updated: ID %d\n", familiaID)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Familia actualizada exitosamente",
	})
}

func asignarUsuarioFamilia(c *gin.Context) {
	fmt.Println("🔍 asignarUsuarioFamilia called")

	var req struct {
		UsuarioID        int    `json:"usuario_id" binding:"required"`
		FamiliaID        int    `json:"familia_id" binding:"required"`
		Relacion         string `json:"relacion"`
		EsAdminFamilia   bool   `json:"es_admin_familia"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos de entrada inválidos"})
		return
	}

	// Usar stored procedure para asignar usuario a familia
	success, err := db.Exec(`SELECT sp_asignar_usuario_familia($1, $2, $3, $4)`,
		req.UsuarioID, req.FamiliaID, req.Relacion, req.EsAdminFamilia)
	
	if err != nil {
		fmt.Printf("❌ Error asignando usuario a familia: %v\n", err)
		c.JSON(500, gin.H{"error": "Error asignando usuario a familia"})
		return
	}

	rowsAffected, _ := success.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(400, gin.H{"error": "No se pudo asignar el usuario a la familia"})
		return
	}

	fmt.Printf("✅ Usuario %d asignado a familia %d\n", req.UsuarioID, req.FamiliaID)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Usuario asignado a familia exitosamente",
	})
}

func removerUsuarioFamilia(c *gin.Context) {
	fmt.Println("🔍 removerUsuarioFamilia called")

	var req struct {
		UsuarioID int `json:"usuario_id" binding:"required"`
		FamiliaID int `json:"familia_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos de entrada inválidos"})
		return
	}

	// Usar stored procedure para remover usuario de familia
	success, err := db.Exec(`SELECT sp_remover_usuario_familia($1, $2)`,
		req.UsuarioID, req.FamiliaID)
	
	if err != nil {
		fmt.Printf("❌ Error removiendo usuario de familia: %v\n", err)
		c.JSON(500, gin.H{"error": "Error removiendo usuario de familia"})
		return
	}

	rowsAffected, _ := success.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(400, gin.H{"error": "No se pudo remover el usuario de la familia"})
		return
	}

	fmt.Printf("✅ Usuario %d removido de familia %d\n", req.UsuarioID, req.FamiliaID)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Usuario removido de familia exitosamente",
	})
}

func deleteFamilia(c *gin.Context) {
	fmt.Println("🔍 deleteFamilia called")
	
	id := c.Param("id")
	familiaID, err := strconv.Atoi(id)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID inválido"})
		return
	}

	// Verificar si la familia existe
	var exists bool
	err = db.QueryRow("SELECT EXISTS(SELECT 1 FROM familias WHERE id = $1)", familiaID).Scan(&exists)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error verificando familia"})
		return
	}

	if !exists {
		c.JSON(404, gin.H{"error": "Familia no encontrada"})
		return
	}

	// Eliminar familia (soft delete - cambiar estado)
	_, err = db.Exec("UPDATE familias SET estado = false WHERE id = $1", familiaID)
	if err != nil {
		fmt.Printf("❌ Error deleting familia: %v\n", err)
		c.JSON(500, gin.H{"error": "Error eliminando familia"})
		return
	}

	// Desactivar todas las membresías de la familia
	_, err = db.Exec("UPDATE miembros_familia SET activo = false WHERE familia_id = $1", familiaID)
	if err != nil {
		fmt.Printf("❌ Error deactivating family memberships: %v\n", err)
	}

	fmt.Printf("✅ Familia deleted: ID %d\n", familiaID)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Familia eliminada exitosamente",
	})
}

// =========================================================
// UBICACIONES - VERSIÓN NORMALIZADA
// =========================================================

func getUbicaciones(c *gin.Context) {
	fmt.Println("🔍 getUbicaciones called")
	
	limit := c.DefaultQuery("limite", "50")
	offset := c.DefaultQuery("offset", "0")
	
	limitInt, _ := strconv.Atoi(limit)
	offsetInt, _ := strconv.Atoi(offset)
	
	// Usar stored procedure para obtener ubicaciones
	query := `SELECT * FROM sp_get_ubicaciones($1, $2, NULL)`
	
	rows, err := db.Query(query, limitInt, offsetInt)
	if err != nil {
		fmt.Printf("❌ Error querying ubicaciones: %v\n", err)
		c.JSON(500, gin.H{"error": "Error consultando ubicaciones", "details": err.Error()})
		return
	}
	defer rows.Close()

	var ubicaciones []map[string]interface{}
	for rows.Next() {
		var u struct {
			ID                  int       `json:"id"`
			UsuarioID           int       `json:"usuario_id"`
			UsuarioNombre       string    `json:"usuario_nombre"`
			Latitud             float64   `json:"latitud"`
			Longitud            float64   `json:"longitud"`
			UbicacionTimestamp  time.Time `json:"ubicacion_timestamp"`
			PrecisionMetros     *int      `json:"precision_metros"`
			Fuente              *string   `json:"fuente"`
		}

		err := rows.Scan(&u.ID, &u.UsuarioID, &u.UsuarioNombre, &u.Latitud, &u.Longitud,
			&u.UbicacionTimestamp, &u.PrecisionMetros, &u.Fuente)
		if err != nil {
			fmt.Printf("❌ Error scanning ubicacion: %v\n", err)
			continue
		}

		ubicaciones = append(ubicaciones, map[string]interface{}{
			"id":                   u.ID,
			"usuario_id":           u.UsuarioID,
			"usuario_nombre":       u.UsuarioNombre,
			"latitud":              u.Latitud,
			"longitud":             u.Longitud,
			"ubicacion_timestamp":  u.UbicacionTimestamp,
			"precision_metros":     u.PrecisionMetros,
			"fuente":               u.Fuente,
		})
	}

	fmt.Printf("✅ Found %d ubicaciones\n", len(ubicaciones))
	c.JSON(200, gin.H{
		"success": true,
		"data":    ubicaciones,
		"total":   len(ubicaciones),
	})
}

func getUbicacionesUsuario(c *gin.Context) {
	fmt.Println("🔍 getUbicacionesUsuario called")
	
	usuarioID := c.Param("usuario_id")
	id, err := strconv.Atoi(usuarioID)
	if err != nil {
		c.JSON(400, gin.H{"error": "ID de usuario inválido"})
		return
	}

	limit := c.DefaultQuery("limite", "50")
	limitInt, _ := strconv.Atoi(limit)
	
	query := `
		SELECT 
			u.id, u.usuario_id, u.latitud, u.longitud, u.timestamp, u.precision_metros, u.fuente
		FROM ubicaciones u
		WHERE u.usuario_id = $1
		ORDER BY u.timestamp DESC
		LIMIT $2
	`
	
	rows, err := db.Query(query, id, limitInt)
	if err != nil {
		fmt.Printf("❌ Error querying ubicaciones usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error consultando ubicaciones del usuario", "details": err.Error()})
		return
	}
	defer rows.Close()

	var ubicaciones []map[string]interface{}
	for rows.Next() {
		var u struct {
			ID              int       `json:"id"`
			UsuarioID       int       `json:"usuario_id"`
			Latitud         float64   `json:"latitud"`
			Longitud        float64   `json:"longitud"`
			Timestamp       time.Time `json:"timestamp"`
			PrecisionMetros *int      `json:"precision_metros"`
			Fuente          string    `json:"fuente"`
		}

		err := rows.Scan(&u.ID, &u.UsuarioID, &u.Latitud, &u.Longitud, &u.Timestamp, &u.PrecisionMetros, &u.Fuente)
		if err != nil {
			fmt.Printf("❌ Error scanning ubicacion usuario: %v\n", err)
			continue
		}

		ubicaciones = append(ubicaciones, map[string]interface{}{
			"id":             u.ID,
			"usuario_id":     u.UsuarioID,
			"latitud":        u.Latitud,
			"longitud":       u.Longitud,
			"timestamp":      u.Timestamp,
			"precision_metros": u.PrecisionMetros,
			"fuente":         u.Fuente,
		})
	}

	fmt.Printf("✅ Found %d ubicaciones for usuario %d\n", len(ubicaciones), id)
	c.JSON(200, gin.H{
		"success": true,
		"data":    ubicaciones,
		"total":   len(ubicaciones),
	})
}