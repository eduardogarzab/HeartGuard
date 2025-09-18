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
	query := `SELECT * FROM sp_get_usuarios($1, $2, $3, $4)`
	
	limit := c.DefaultQuery("limite", "50")
	offset := c.DefaultQuery("offset", "0")
	rolID := c.Query("rol_id")
	familiaID := c.Query("familia_id")
	
	limitInt, _ := strconv.Atoi(limit)
	offsetInt, _ := strconv.Atoi(offset)
	
	var rolIDInt *int
	var familiaIDInt *int
	
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
	
	rows, err := db.Query(query, limitInt, offsetInt, rolIDInt, familiaIDInt)
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
		}

		err := rows.Scan(&u.ID, &u.Nombre, &u.Email, &u.RolNombre, &u.FamiliaNombre, 
			&u.Relacion, &u.EsAdminFamilia, &u.UltimaActualizacion, &u.FechaCreacion)
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
		RETURNING id, nombre, email, rol_id, fecha_creacion
	`
	
	var u struct {
		ID            int       `json:"id"`
		Nombre        string    `json:"nombre"`
		Email         string    `json:"email"`
		RolID         int       `json:"rol_id"`
		FechaCreacion time.Time `json:"fecha_creacion"`
	}

	err = db.QueryRow(query, req.Nombre, req.Email, string(hashedPassword), rolID).
		Scan(&u.ID, &u.Nombre, &u.Email, &u.RolID, &u.FechaCreacion)
	
	if err != nil {
		fmt.Printf("❌ Error inserting usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error creando usuario", "details": err.Error()})
		return
	}

	// Si se especificó familia, asignar al usuario
	if req.FamiliaID != nil {
		updateFamiliaQuery := `UPDATE usuarios SET familia_id = $1 WHERE id = $2`
		_, err = db.Exec(updateFamiliaQuery, *req.FamiliaID, u.ID)
		if err != nil {
			fmt.Printf("❌ Error assigning user to family: %v\n", err)
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
			u.fecha_creacion, u.ultima_actualizacion,
			r.nombre as rol_nombre,
			COALESCE(f.nombre_familia, 'Sin familia') as familia_nombre,
			u.familia_id,
			NULL as relacion, NULL as es_admin_familia
		FROM usuarios u
		JOIN roles r ON u.rol_id = r.id
		LEFT JOIN familias f ON u.familia_id = f.id
		WHERE u.id = $1
	`
	
	var u struct {
		ID                int       `json:"id"`
		Nombre            string    `json:"nombre"`
		Email             string    `json:"email"`
		Latitud           *float64  `json:"latitud"`
		Longitud          *float64  `json:"longitud"`
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
		&u.FechaCreacion, &u.UltimaActualizacion,
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
		RemoveFromFamily *bool `json:"remove_from_family"`
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
    // Añadir lógica para actualizar familia_id en la misma query
    if req.FamiliaID != nil {
        if *req.FamiliaID == 0 { // Asumimos que 0 o un valor nulo significa "Sin Familia"
            setParts = append(setParts, fmt.Sprintf("familia_id = NULL"))
        } else {
            setParts = append(setParts, fmt.Sprintf("familia_id = $%d", argIndex))
            args = append(args, *req.FamiliaID)
            argIndex++
        }
    }


	if len(setParts) == 0 {
		c.JSON(400, gin.H{"error": "No hay campos para actualizar"})
		return
	}

	setParts = append(setParts, "ultima_actualizacion = CURRENT_TIMESTAMP")
	args = append(args, usuarioID)

	query := fmt.Sprintf("UPDATE usuarios SET %s WHERE id = $%d RETURNING id, nombre, email, rol_id, ultima_actualizacion",
		strings.Join(setParts, ", "), len(args))

	var u struct {
		ID                 int       `json:"id"`
		Nombre             string    `json:"nombre"`
		Email              string    `json:"email"`
		RolID              int       `json:"rol_id"`
		UltimaActualizacion time.Time `json:"ultima_actualizacion"`
	}

	err = db.QueryRow(query, args...).Scan(&u.ID, &u.Nombre, &u.Email, &u.RolID, &u.UltimaActualizacion)
	if err != nil {
		fmt.Printf("❌ Error updating usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error actualizando usuario"})
		return
	}

	// La lógica de actualización de familia separada se puede eliminar o comentar
	/*
	// Actualizar familia del usuario si se especificó
	if req.FamiliaID != nil || req.RemoveFromFamily != nil {
		if req.RemoveFromFamily != nil && *req.RemoveFromFamily {
			// Remover de la familia (establecer familia_id como NULL)
			setFamiliaQuery := `UPDATE usuarios SET familia_id = NULL WHERE id = $1`
			_, err = db.Exec(setFamiliaQuery, usuarioID)
			if err != nil {
				fmt.Printf("❌ Error removing from family: %v\n", err)
			}
		} else if req.FamiliaID != nil {
			// Asignar a la familia especificada
			setFamiliaQuery := `UPDATE usuarios SET familia_id = $1 WHERE id = $2`
			_, err = db.Exec(setFamiliaQuery, *req.FamiliaID, usuarioID)
			if err != nil {
				fmt.Printf("❌ Error setting family: %v\n", err)
			}
		}
	}
	*/

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


	// Eliminar usuario completamente (hard delete con cascada)
	// Eliminar alertas del usuario
	_, err = db.Exec("DELETE FROM alertas WHERE usuario_id = $1", usuarioID)
	if err != nil {
		fmt.Printf("❌ Error deleting user alerts: %v\n", err)
		c.JSON(500, gin.H{"error": "Error eliminando alertas del usuario"})
		return
	}

	// Eliminar logs del usuario
	_, err = db.Exec("DELETE FROM logs_sistema WHERE usuario_id = $1", usuarioID)
	if err != nil {
		fmt.Printf("❌ Error deleting user logs: %v\n", err)
		c.JSON(500, gin.H{"error": "Error eliminando logs del usuario"})
		return
	}

	// Finalmente eliminar el usuario
	_, err = db.Exec("DELETE FROM usuarios WHERE id = $1", usuarioID)
	if err != nil {
		fmt.Printf("❌ Error deleting usuario: %v\n", err)
		c.JSON(500, gin.H{"error": "Error eliminando usuario"})
		return
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
	query := `SELECT * FROM sp_get_familias($1, $2)`
	
	limit := c.DefaultQuery("limite", "50")
	offset := c.DefaultQuery("offset", "0")
	
	limitInt, _ := strconv.Atoi(limit)
	offsetInt, _ := strconv.Atoi(offset)
	
	rows, err := db.Query(query, limitInt, offsetInt)
	if err != nil {
		fmt.Printf("❌ Error querying familias: %v\n", err)
		c.JSON(500, gin.H{"error": "Error consultando familias", "details": err.Error()})
		return
	}
	defer rows.Close()

	familias := make([]map[string]interface{}, 0)
	for rows.Next() {
		var f struct {
			ID            int       `json:"id"`
			NombreFamilia string    `json:"nombre_familia"`
			CodigoFamilia *string   `json:"codigo_familia"`
			FechaCreacion time.Time `json:"fecha_creacion"`
			TotalMiembros int64     `json:"total_miembros"`
			TotalAdmins   int64     `json:"total_admins"`
		}

		err := rows.Scan(&f.ID, &f.NombreFamilia, &f.CodigoFamilia, &f.FechaCreacion, &f.TotalMiembros, &f.TotalAdmins)
		if err != nil {
			fmt.Printf("❌ Error scanning familia: %v\n", err)
			continue
		}

		familias = append(familias, map[string]interface{}{
			"id":              f.ID,
			"nombre_familia":  f.NombreFamilia,
			"codigo_familia":  f.CodigoFamilia,
			"fecha_creacion":  f.FechaCreacion,
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
		Descripcion   string `json:"descripcion"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("❌ Error binding request: %v\n", err)
		c.JSON(400, gin.H{"error": "Datos inválidos", "details": err.Error()})
		return
	}

	// Usar stored procedure para crear familia
	var codigoFamilia *string
	var descripcion *string
	
	if req.CodigoFamilia != "" {
		codigoFamilia = &req.CodigoFamilia
	}
	
	if req.Descripcion != "" {
		descripcion = &req.Descripcion
	}

	rows, err := db.Query(`SELECT * FROM sp_create_familia($1, $2, $3)`, req.NombreFamilia, codigoFamilia, descripcion)
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
			f.id, f.nombre_familia, f.codigo_familia, f.fecha_creacion,
			COUNT(u.id) as total_miembros,
			COUNT(CASE WHEN u.rol_id = (SELECT r.id FROM roles r WHERE r.nombre = 'admin_familia') THEN 1 END) as total_admins
		FROM familias f
		LEFT JOIN usuarios u ON f.id = u.familia_id
		WHERE f.id = $1
		GROUP BY f.id, f.nombre_familia, f.codigo_familia, f.fecha_creacion
	`
	
	var f struct {
		ID            int       `json:"id"`
		NombreFamilia string    `json:"nombre_familia"`
		CodigoFamilia *string   `json:"codigo_familia"`
		FechaCreacion time.Time `json:"fecha_creacion"`
		TotalMiembros int       `json:"total_miembros"`
		TotalAdmins   int       `json:"total_admins"`
	}

	err = db.QueryRow(query, familiaID).Scan(&f.ID, &f.NombreFamilia, &f.CodigoFamilia, &f.FechaCreacion, &f.TotalMiembros, &f.TotalAdmins)
	
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
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Usar stored procedure para actualizar familia
	rows, err := db.Query(`SELECT sp_update_familia($1, $2, $3)`, 
		familiaID, req.NombreFamilia, req.CodigoFamilia)
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

	// Primero cambiar usuarios admin_familia a miembro y quitar de la familia
	_, err = db.Exec(`
		UPDATE usuarios 
		SET rol_id = (SELECT id FROM roles WHERE nombre = 'miembro'),
		    familia_id = NULL
		WHERE familia_id = $1 AND rol_id = (SELECT id FROM roles WHERE nombre = 'admin_familia')
	`, familiaID)
	if err != nil {
		fmt.Printf("❌ Error updating admin_familia users: %v\n", err)
		c.JSON(500, gin.H{"error": "Error actualizando administradores de familia"})
		return
	}

	// Quitar a todos los usuarios de la familia
	_, err = db.Exec("UPDATE usuarios SET familia_id = NULL WHERE familia_id = $1", familiaID)
	if err != nil {
		fmt.Printf("❌ Error removing users from family: %v\n", err)
		c.JSON(500, gin.H{"error": "Error removiendo usuarios de la familia"})
		return
	}

	// Finalmente eliminar la familia
	_, err = db.Exec("DELETE FROM familias WHERE id = $1", familiaID)
	if err != nil {
		fmt.Printf("❌ Error deleting familia: %v\n", err)
		c.JSON(500, gin.H{"error": "Error eliminando familia"})
		return
	}

	fmt.Printf("✅ Familia deleted: ID %d\n", familiaID)
	c.JSON(200, gin.H{
		"success": true,
		"message": "Familia eliminada exitosamente",
	})
}


// =========================================================
// Funciones CRUD para Catálogos
// =========================================================

type Catalogo struct {
	ID          int    `json:"id" db:"id"`
	Tipo        string `json:"tipo" db:"tipo"`
	Clave       string `json:"clave" db:"clave"`
	Valor       string `json:"valor" db:"valor"`
	Descripcion string `json:"descripcion" db:"descripcion"`
	Activo      bool   `json:"activo" db:"activo"`
	FechaCreacion string `json:"fecha_creacion" db:"fecha_creacion"`
}

type CreateCatalogoRequest struct {
	Tipo        string `json:"tipo" binding:"required"`
	Clave       string `json:"clave" binding:"required"`
	Valor       string `json:"valor" binding:"required"`
	Descripcion string `json:"descripcion"`
	Activo      bool   `json:"activo"`
}

type UpdateCatalogoRequest struct {
	Tipo        string `json:"tipo"`
	Clave       string `json:"clave"`
	Valor       string `json:"valor"`
	Descripcion string `json:"descripcion"`
	Activo      bool   `json:"activo"`
}

func getCatalogos(c *gin.Context) {
	fmt.Println("📋 Getting catalogos...")
	
	query := `
		SELECT id, tipo, clave, valor, descripcion, activo, 
		       TO_CHAR(fecha_creacion, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as fecha_creacion
		FROM catalogos 
		ORDER BY tipo, clave
	`
	
	rows, err := db.Query(query)
	if err != nil {
		fmt.Printf("❌ Error getting catalogos: %v\n", err)
		c.JSON(500, gin.H{"success": false, "error": "Error al obtener catálogos"})
		return
	}
	defer rows.Close()
	
	var catalogos []Catalogo
	for rows.Next() {
		var catalogo Catalogo
		err := rows.Scan(&catalogo.ID, &catalogo.Tipo, &catalogo.Clave, &catalogo.Valor, &catalogo.Descripcion, &catalogo.Activo, &catalogo.FechaCreacion)
		if err != nil {
			fmt.Printf("❌ Error scanning catalogo: %v\n", err)
			c.JSON(500, gin.H{"success": false, "error": "Error al procesar catálogos"})
			return
		}
		catalogos = append(catalogos, catalogo)
	}
	
	fmt.Printf("✅ Found %d catalogos\n", len(catalogos))
	c.JSON(200, gin.H{
		"success": true,
		"data":    catalogos,
		"total":   len(catalogos),
	})
}

func getCatalogo(c *gin.Context) {
	fmt.Println("📋 Getting single catalogo...")
	
	id := c.Param("id")
	query := `
		SELECT id, tipo, clave, valor, descripcion, activo, 
		       TO_CHAR(fecha_creacion, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as fecha_creacion
		FROM catalogos 
		WHERE id = $1
	`
	
	var catalogo Catalogo
	err := db.QueryRow(query, id).Scan(&catalogo.ID, &catalogo.Tipo, &catalogo.Clave, &catalogo.Valor, &catalogo.Descripcion, &catalogo.Activo, &catalogo.FechaCreacion)
	if err != nil {
		fmt.Printf("❌ Error getting catalogo: %v\n", err)
		c.JSON(404, gin.H{"success": false, "error": "Catálogo no encontrado"})
		return
	}
	
	fmt.Printf("✅ Found catalogo with ID: %s\n", id)
	c.JSON(200, gin.H{
		"success": true,
		"data":    catalogo,
	})
}

func createCatalogo(c *gin.Context) {
	fmt.Println("📝 Creating catalogo...")
	
	var req CreateCatalogoRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("❌ Error binding JSON: %v\n", err)
		c.JSON(400, gin.H{"success": false, "error": "Datos inválidos"})
		return
	}
	
	query := `
		INSERT INTO catalogos (tipo, clave, valor, descripcion, activo)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING id
	`
	
	var id int
	err := db.QueryRow(query, req.Tipo, req.Clave, req.Valor, req.Descripcion, req.Activo).Scan(&id)
	if err != nil {
		fmt.Printf("❌ Error creating catalogo: %v\n", err)
		c.JSON(500, gin.H{"success": false, "error": "Error al crear catálogo"})
		return
	}
	
	fmt.Printf("✅ Created catalogo with ID: %d\n", id)
	c.JSON(201, gin.H{"success": true, "id": id})
}

func updateCatalogo(c *gin.Context) {
	fmt.Println("✏️ Updating catalogo...")
	
	id := c.Param("id")
	var req UpdateCatalogoRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("❌ Error binding JSON: %v\n", err)
		c.JSON(400, gin.H{"success": false, "error": "Datos inválidos"})
		return
	}
	
	// Build dynamic query
	setParts := []string{}
	args := []interface{}{}
	argIndex := 1
	
	if req.Tipo != "" {
		setParts = append(setParts, fmt.Sprintf("tipo = $%d", argIndex))
		args = append(args, req.Tipo)
		argIndex++
	}
	if req.Clave != "" {
		setParts = append(setParts, fmt.Sprintf("clave = $%d", argIndex))
		args = append(args, req.Clave)
		argIndex++
	}
	if req.Valor != "" {
		setParts = append(setParts, fmt.Sprintf("valor = $%d", argIndex))
		args = append(args, req.Valor)
		argIndex++
	}
	if req.Descripcion != "" {
		setParts = append(setParts, fmt.Sprintf("descripcion = $%d", argIndex))
		args = append(args, req.Descripcion)
		argIndex++
	}
	
	setParts = append(setParts, fmt.Sprintf("activo = $%d", argIndex))
	args = append(args, req.Activo)
	argIndex++
	
	args = append(args, id)
	
	query := fmt.Sprintf("UPDATE catalogos SET %s WHERE id = $%d", strings.Join(setParts, ", "), argIndex)
	
	result, err := db.Exec(query, args...)
	if err != nil {
		fmt.Printf("❌ Error updating catalogo: %v\n", err)
		c.JSON(500, gin.H{"success": false, "error": "Error al actualizar catálogo"})
		return
	}
	
	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"success": false, "error": "Catálogo no encontrado"})
		return
	}
	
	fmt.Printf("✅ Updated catalogo with ID: %s\n", id)
	c.JSON(200, gin.H{"success": true})
}

func deleteCatalogo(c *gin.Context) {
	fmt.Println("🗑️ Deleting catalogo...")
	
	id := c.Param("id")
	query := "DELETE FROM catalogos WHERE id = $1"
	
	result, err := db.Exec(query, id)
	if err != nil {
		fmt.Printf("❌ Error deleting catalogo: %v\n", err)
		c.JSON(500, gin.H{"success": false, "error": "Error al eliminar catálogo"})
		return
	}
	
	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"success": false, "error": "Catálogo no encontrado"})
		return
	}
	
	fmt.Printf("✅ Deleted catalogo with ID: %s\n", id)
	c.JSON(200, gin.H{"success": true})
}
