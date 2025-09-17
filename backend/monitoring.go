package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
)

// Estructuras para alertas
type Alerta struct {
	ID            int       `json:"id"`
	UsuarioID     int       `json:"usuario_id"`
	UsuarioNombre string    `json:"usuario_nombre,omitempty"`
	FamiliaNombre string    `json:"familia_nombre,omitempty"`
	Tipo          string    `json:"tipo"`
	Descripcion   string    `json:"descripcion"`
	Nivel         string    `json:"nivel"`
	Fecha         time.Time `json:"fecha"`
	Atendida      bool      `json:"atendida"`
	FechaAtencion *time.Time `json:"fecha_atencion,omitempty"`
	AtendidoPor   *int      `json:"atendido_por,omitempty"`
}

type CreateAlertaRequest struct {
	UsuarioID    int    `json:"usuario_id" binding:"required"`
	Tipo         string `json:"tipo" binding:"required"`
	Descripcion  string `json:"descripcion" binding:"required"`
	Nivel        string `json:"nivel" binding:"required"`
}

type AtenderAlertaRequest struct {
	AtendidoPor int `json:"atendido_por" binding:"required"`
}


// Estructuras para logs del sistema
type LogSistema struct {
	ID          int       `json:"id"`
	UsuarioID   *int      `json:"usuario_id,omitempty"`
	Accion      string    `json:"accion"`
	Detalle     string    `json:"detalle"`
	Fecha       time.Time `json:"fecha"`
	UsuarioNombre *string `json:"usuario_nombre,omitempty"`
}

// Estructuras para microservicios
type Microservicio struct {
	ID          int       `json:"id"`
	Nombre      string    `json:"nombre"`
	URL         string    `json:"url"`
	Estado      string    `json:"estado"`
	UltimaVerificacion *time.Time `json:"ultima_verificacion,omitempty"`
	Version     *string   `json:"version,omitempty"`
}

type UpdateEstadoMicroservicioRequest struct {
	Estado string `json:"estado" binding:"required"`
}

// =========================================================
// CRUD ALERTAS
// =========================================================

func createAlerta(c *gin.Context) {
	var req CreateAlertaRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Usar stored procedure para crear alerta
	rows, err := db.Query(`SELECT * FROM sp_create_alerta($1, $2, $3, $4)`, 
		req.UsuarioID, req.Tipo, req.Descripcion, req.Nivel)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error creando alerta"})
		return
	}
	defer rows.Close()

	var alertaID int
	var fecha time.Time
	if rows.Next() {
		err = rows.Scan(&alertaID, &fecha)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error obteniendo datos de la alerta creada"})
			return
		}
	}

	// Registrar log
	superAdminID, _ := c.Get("usuario_id")
	registrarLog(superAdminID.(int), "CREATE_ALERTA", fmt.Sprintf(`{"alerta_id": %d, "usuario_id": %d, "tipo": "%s"}`, alertaID, req.UsuarioID, req.Tipo))

	c.JSON(201, gin.H{
		"success": true,
		"data": gin.H{
			"id":    alertaID,
			"fecha": fecha,
		},
		"message": "Alerta creada exitosamente",
	})
}

func getAlertas(c *gin.Context) {
	// Usar stored procedure para obtener alertas
	rows, err := db.Query(`SELECT * FROM sp_get_alertas()`)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando alertas"})
		return
	}
	defer rows.Close()

	var alertas []Alerta
	for rows.Next() {
		var alerta Alerta
		var fechaAtencion sql.NullTime
		var atendidoPor sql.NullInt64
		var usuarioNombre, familiaNombre sql.NullString

		err := rows.Scan(&alerta.ID, &alerta.UsuarioID, &usuarioNombre, &familiaNombre,
			&alerta.Tipo, &alerta.Descripcion, &alerta.Nivel, &alerta.Fecha, 
			&alerta.Atendida, &fechaAtencion, &atendidoPor)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando alertas"})
			return
		}

		if usuarioNombre.Valid {
			alerta.UsuarioNombre = usuarioNombre.String
		}
		if familiaNombre.Valid {
			alerta.FamiliaNombre = familiaNombre.String
		}
		if fechaAtencion.Valid {
			alerta.FechaAtencion = &fechaAtencion.Time
		}
		if atendidoPor.Valid {
			atendidoPorInt := int(atendidoPor.Int64)
			alerta.AtendidoPor = &atendidoPorInt
		}

		alertas = append(alertas, alerta)
	}

	c.JSON(200, gin.H{
		"success": true,
		"data":    alertas,
		"total":   len(alertas),
	})
}

func getAlertasUsuario(c *gin.Context) {
	usuarioID := c.Param("id")
	limit := c.DefaultQuery("limit", "50")
	
	// Query para obtener alertas de un usuario específico
	query := `SELECT a.id, a.usuario_id, u.nombre as usuario_nombre, f.nombre_familia,
			  a.tipo, a.descripcion, a.nivel, a.fecha, a.atendida, a.fecha_atencion, a.atendido_por
			  FROM alertas a
			  JOIN usuarios u ON a.usuario_id = u.id
			  LEFT JOIN familias f ON u.familia_id = f.id
			  WHERE a.usuario_id = $1
			  ORDER BY a.fecha DESC
			  LIMIT $2`
	
	rows, err := db.Query(query, usuarioID, limit)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando alertas del usuario"})
		return
	}
	defer rows.Close()

	var alertas []Alerta
	for rows.Next() {
		var alerta Alerta
		var fechaAtencion sql.NullTime
		var atendidoPor sql.NullInt64
		var usuarioNombre, familiaNombre sql.NullString

		err := rows.Scan(&alerta.ID, &alerta.UsuarioID, &usuarioNombre, &familiaNombre,
			&alerta.Tipo, &alerta.Descripcion, &alerta.Nivel, &alerta.Fecha, 
			&alerta.Atendida, &fechaAtencion, &atendidoPor)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando alertas"})
			return
		}

		if usuarioNombre.Valid {
			alerta.UsuarioNombre = usuarioNombre.String
		}
		if familiaNombre.Valid {
			alerta.FamiliaNombre = familiaNombre.String
		}
		if fechaAtencion.Valid {
			alerta.FechaAtencion = &fechaAtencion.Time
		}
		if atendidoPor.Valid {
			atendidoPorInt := int(atendidoPor.Int64)
			alerta.AtendidoPor = &atendidoPorInt
		}

		alertas = append(alertas, alerta)
	}

	c.JSON(200, gin.H{
		"success": true,
		"data":    alertas,
		"total":   len(alertas),
	})
}

func atenderAlerta(c *gin.Context) {
	alertaID := c.Param("id")
	var req AtenderAlertaRequest
	
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Usar stored procedure para atender alerta
	rows, err := db.Query(`SELECT sp_atender_alerta($1, $2)`, alertaID, req.AtendidoPor)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error atendiendo alerta"})
		return
	}
	defer rows.Close()

	var success bool
	if rows.Next() {
		err = rows.Scan(&success)
		if err != nil || !success {
			c.JSON(404, gin.H{"error": "Alerta no encontrada"})
			return
		}
	}

	// Registrar log
	superAdminID, _ := c.Get("usuario_id")
	registrarLog(superAdminID.(int), "ATENDER_ALERTA", fmt.Sprintf(`{"alerta_id": %s, "atendido_por": %d}`, alertaID, req.AtendidoPor))

	c.JSON(200, gin.H{
		"success": true,
		"message": "Alerta atendida exitosamente",
	})
}

func deleteAlerta(c *gin.Context) {
	alertaID := c.Param("id")
	
	// Eliminar alerta (soft delete marcando como atendida)
	query := `UPDATE alertas SET atendida = true, fecha_atencion = CURRENT_TIMESTAMP 
			  WHERE id = $1`
	result, err := db.Exec(query, alertaID)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error eliminando alerta"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(404, gin.H{"error": "Alerta no encontrada"})
		return
	}

	// Registrar log
	superAdminID, _ := c.Get("usuario_id")
	registrarLog(superAdminID.(int), "DELETE_ALERTA", fmt.Sprintf(`{"alerta_id": %s}`, alertaID))

	c.JSON(200, gin.H{
		"success": true,
		"message": "Alerta eliminada exitosamente",
	})
}


// =========================================================
// LOGS DEL SISTEMA
// =========================================================

func getLogsSistema(c *gin.Context) {
	fmt.Println("🔍 getLogsSistema called")

	// Consulta directa para obtener logs
	query := `
		SELECT l.id, l.usuario_id, COALESCE(u.nombre, 'Sistema') as usuario_nombre,
		       l.accion, l.detalle, TO_CHAR(l.fecha, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as fecha
		FROM logs_sistema l
		LEFT JOIN usuarios u ON l.usuario_id = u.id
		ORDER BY l.fecha DESC
		LIMIT 100
	`

	rows, err := db.Query(query)
	if err != nil {
		fmt.Printf("❌ Error querying logs: %v\n", err)
		c.JSON(500, gin.H{"error": "Error consultando logs del sistema"})
		return
	}
	defer rows.Close()

	var logs []map[string]interface{}
	for rows.Next() {
		var log struct {
			ID            int     `json:"id"`
			UsuarioID     *int    `json:"usuario_id"`
			UsuarioNombre string  `json:"usuario_nombre"`
			Accion        string  `json:"accion"`
			Detalle       string  `json:"detalle"`
			Fecha         string  `json:"fecha"`
		}

		err := rows.Scan(&log.ID, &log.UsuarioID, &log.UsuarioNombre, &log.Accion, 
			&log.Detalle, &log.Fecha)
		if err != nil {
			fmt.Printf("❌ Error scanning log: %v\n", err)
			continue
		}

		usuarioID := 0
		if log.UsuarioID != nil {
			usuarioID = *log.UsuarioID
		}

		logs = append(logs, map[string]interface{}{
			"id":            log.ID,
			"usuario_id":    usuarioID,
			"usuario_nombre": log.UsuarioNombre,
			"accion":        log.Accion,
			"detalle":       log.Detalle,
			"fecha":         log.Fecha,
		})
	}

	fmt.Printf("✅ Found %d logs\n", len(logs))
	c.JSON(200, gin.H{
		"success": true,
		"data":    logs,
		"total":   len(logs),
	})
}

// =========================================================
// MONITOREO DE MICROSERVICIOS
// =========================================================

func getDashboardStats(c *gin.Context) {
	fmt.Println("🔍 getDashboardStats called")

	// Usar stored procedure para obtener estadísticas del dashboard
	query := `SELECT * FROM sp_dashboard_ejecutivo()`

	row := db.QueryRow(query)
	var stats struct {
		TotalUsuarios     int64 `json:"total_usuarios"`
		TotalFamilias     int64 `json:"total_familias"`
		AlertasPendientes int64 `json:"alertas_pendientes"`
		AlertasCriticas   int64 `json:"alertas_criticas"`
		UbicacionesHoy    int64 `json:"ubicaciones_hoy"`
		MicroserviciosActivos int64 `json:"microservicios_activos"`
	}

	err := row.Scan(&stats.TotalUsuarios, &stats.TotalFamilias, &stats.AlertasPendientes,
		&stats.AlertasCriticas, &stats.UbicacionesHoy, &stats.MicroserviciosActivos)
	if err != nil {
		fmt.Printf("❌ Error querying dashboard stats: %v\n", err)
		c.JSON(500, gin.H{"error": "Error obteniendo estadísticas"})
		return
	}

	fmt.Printf("✅ Dashboard stats retrieved: %+v\n", stats)
	c.JSON(200, gin.H{
		"success": true,
		"data":    stats,
	})
}

func getHealthMicroservicios(c *gin.Context) {
	// Consultar estado de microservicios
	query := `SELECT id, nombre, url, estado, ultima_verificacion, version 
			  FROM microservicios ORDER BY nombre`
	
	rows, err := db.Query(query)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error consultando microservicios"})
		return
	}
	defer rows.Close()

	var microservicios []Microservicio
	for rows.Next() {
		var microservicio Microservicio
		var ultimaVerificacion sql.NullTime
		var version sql.NullString

		err := rows.Scan(&microservicio.ID, &microservicio.Nombre, &microservicio.URL, 
			&microservicio.Estado, &ultimaVerificacion, &version)
		if err != nil {
			c.JSON(500, gin.H{"error": "Error escaneando microservicios"})
			return
		}

		if ultimaVerificacion.Valid {
			microservicio.UltimaVerificacion = &ultimaVerificacion.Time
		}
		if version.Valid {
			microservicio.Version = &version.String
		}

		microservicios = append(microservicios, microservicio)
	}

	c.JSON(200, gin.H{
		"success": true,
		"data":    microservicios,
		"total":   len(microservicios),
	})
}

func updateEstadoMicroservicio(c *gin.Context) {
	microservicioID := c.Param("id")
	var req UpdateEstadoMicroservicioRequest
	
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "Datos inválidos"})
		return
	}

	// Validar estado
	if req.Estado != "activo" && req.Estado != "inactivo" && req.Estado != "error" {
		c.JSON(400, gin.H{"error": "Estado inválido. Debe ser: activo, inactivo o error"})
		return
	}

	// Usar stored procedure para actualizar estado
	rows, err := db.Query(`SELECT actualizar_estado_microservicio($1, $2)`, 
		microservicioID, req.Estado)
	if err != nil {
		c.JSON(500, gin.H{"error": "Error actualizando estado del microservicio"})
		return
	}
	defer rows.Close()

	var success bool
	if rows.Next() {
		err = rows.Scan(&success)
		if err != nil || !success {
			c.JSON(404, gin.H{"error": "Microservicio no encontrado"})
			return
		}
	}

	// Registrar log
	superAdminID, _ := c.Get("usuario_id")
	registrarLog(superAdminID.(int), "UPDATE_MICROSERVICIO", fmt.Sprintf(`{"microservicio_id": %s, "estado": "%s"}`, microservicioID, req.Estado))

	c.JSON(200, gin.H{
		"success": true,
		"message": "Estado del microservicio actualizado exitosamente",
	})
}

// =========================================================
// MÉTRICAS (PLACEHOLDER - VAN A INFLUXDB)
// =========================================================

func getMetricas(c *gin.Context) {
	// Placeholder - las métricas se consultan desde InfluxDB
	// Esto se implementará cuando esté listo el microservicio Flask
	c.JSON(200, gin.H{
		"success": true,
		"data":    []interface{}{},
		"total":   0,
		"message": "Métricas se consultan desde InfluxDB vía microservicio Flask",
	})
}

func createMetrica(c *gin.Context) {
	// Placeholder - las métricas se insertan en InfluxDB
	// Esto se implementará cuando esté listo el microservicio Flask
	c.JSON(501, gin.H{
		"error": "Las métricas se insertan directamente en InfluxDB desde el dispositivo móvil vía microservicio Flask",
	})
}

func getMetricasUsuario(c *gin.Context) {
	// Placeholder - las métricas se consultan desde InfluxDB
	// Esto se implementará cuando esté listo el microservicio Flask
	c.JSON(200, gin.H{
		"success": true,
		"data":    []interface{}{},
		"total":   0,
		"message": "Métricas se consultan desde InfluxDB vía microservicio Flask",
	})
}

func deleteMetrica(c *gin.Context) {
	// Placeholder - las métricas se eliminan desde InfluxDB
	// Esto se implementará cuando esté listo el microservicio Flask
	c.JSON(501, gin.H{
		"error": "Las métricas se eliminan directamente en InfluxDB",
	})
}// =========================================================
// FUNCIONES AUXILIARES
// =========================================================

func registrarLog(usuarioID int, accion string, detalle string) {
	// Convertir detalle a JSON si es necesario
	var detalleJSON string
	if detalle != "" {
		// Intentar parsear como JSON para validar
		var jsonData interface{}
		if err := json.Unmarshal([]byte(detalle), &jsonData); err == nil {
			detalleJSON = detalle
		} else {
			// Si no es JSON válido, crear un JSON simple
			detalleJSON = fmt.Sprintf(`{"mensaje": "%s"}`, detalle)
		}
	} else {
		detalleJSON = "{}"
	}

	// Insertar log usando stored procedure
	_, err := db.Exec(`SELECT registrar_log_sistema($1, $2, $3)`, 
		usuarioID, accion, detalleJSON)
	if err != nil {
		// Log del error pero no fallar la operación principal
		fmt.Printf("Error registrando log: %v\n", err)
	}
}


