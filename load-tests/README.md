# HeartGuard - Load Testing

Pruebas de carga y rendimiento para la plataforma HeartGuard.

## 📁 Estructura

```
load-tests/
└── locust/              # Suite completa de pruebas Locust
    ├── README.md        # Documentación completa
    ├── QUICKSTART.md    # Guía de inicio rápido
    ├── setup.ps1        # Script de instalación
    └── *.py             # Archivos de prueba
```

## 🚀 Inicio Rápido

### 1. Navegar al directorio de Locust

```powershell
cd locust
```

### 2. Ejecutar setup

```powershell
.\setup.ps1
```

### 3. Configurar credenciales

Editar `locust/config.py` con tus credenciales de prueba.

### 4. Ejecutar primera prueba

```powershell
locust -f smoke_test.py --host=http://129.212.181.53:8080 --users=5 --spawn-rate=5 --run-time=1m --headless
```

## 📚 Documentación

Para documentación completa, consulta:
- **[locust/README.md](locust/README.md)** - Documentación detallada
- **[locust/QUICKSTART.md](locust/QUICKSTART.md)** - Guía de inicio rápido

## 🧪 Tipos de Pruebas Disponibles

1. **Baseline** - Latencias bajo carga ligera
2. **Smoke** - Verificación rápida de servicios
3. **Read-Heavy** - Operaciones de lectura intensivas
4. **Write-Heavy** - Operaciones de escritura concurrentes
5. **Ramp** - Carga gradual creciente/decreciente
6. **Spike** - Picos súbitos de tráfico
7. **Soak** - Estabilidad sostenida (1-4 horas)
8. **Breakpoint** - Capacidad máxima del sistema

## 🎯 Casos de Uso Comunes

### Después de un Deploy
```powershell
cd locust
locust -f smoke_test.py --host=http://129.212.181.53:8080 --users=5 --spawn-rate=5 --run-time=1m --headless
```

### Suite Completa Pre-Release
```powershell
cd locust
.\run_all_tests.ps1
```

### Suite Rápida (20 minutos)
```powershell
cd locust
.\run_quick_tests.ps1
```

## 📊 Tecnología

- **[Locust](https://locust.io/)** - Framework de pruebas de carga en Python
- Enfoque en microservicios de HeartGuard
- Gateway: `http://129.212.181.53:8080`

## 🔗 Enlaces Útiles

- [Locust Documentation](https://docs.locust.io/)
- [HeartGuard Gateway](http://129.212.181.53:8080/health/)

---

**Nota**: Siempre coordina con el equipo antes de ejecutar pruebas de carga grandes.
