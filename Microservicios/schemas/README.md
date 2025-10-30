# Heartguard Schemas

Este directorio contiene esquemas JSON Schema y XSD para validar los payloads principales de los microservicios. Cada servicio incluye ganchos para utilizarlos con librerías como `jsonschema` o validadores XML cuando se requiera.

| Recurso       | JSON Schema                 | XML Schema |
|---------------|----------------------------|------------|
| Usuario       | `user.schema.json`          | `user.xsd` |
| Organización  | `organization.schema.json`  | `organization.xsd` |
| Token Auth    | `auth_token.schema.json`    | `auth_token.xsd` |
| Media         | `media_item.schema.json`    | `media_item.xsd` |
| Series de tiempo | `timeseries.schema.json` | `timeseries.xsd` |

Los esquemas XSD están diseñados para representar estructuras equivalentes a los JSON Schema correspondientes.

