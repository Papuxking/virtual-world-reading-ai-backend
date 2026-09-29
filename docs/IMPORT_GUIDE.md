# Import Guide — Importar lecturas desde .txt

## Requisitos

- Python 3.10+
- Paquete `requests` (`pip install requests`)
- API corriendo en `http://localhost:8000`

## Estructura de carpetas esperada

```
readings/
├── Descriptivo/
│   ├── bannos.txt
│   └── mi lectura.txt
├── Narrativo/
│   └── relato corto.txt
├── Argumentativo/
│   └── ensayo opinión.txt
└── Expositivo/
    └── el sistema solar.txt
```

### Convenciones

- **Tipología**: inferida del nombre de la subcarpeta (case-insensitive)
- Solo se aceptan las 4 tipologías del juego (Narrativo, Descriptivo, Argumentativo, Expositivo).
- **Título**: inferido del nombre del archivo sin extensión (capitalizado con `.title()`)
- **Contenido mínimo**: 100 caracteres (lecturas más cortas se omiten)
- **Carpeta "Test"**: se omite automáticamente (tipología no reconocida)

## Uso

### Desde carpeta

```bash
cd Docker/api

# Importar desde la carpeta de lecturas del proyecto Godot
python import_readings.py \
  --folder "../../virtual-world-reading-ai/readings" \
  --api-url http://localhost:8000
```

### Desde archivo ZIP

```bash
python import_readings.py \
  --zip lecturas.zip \
  --api-url http://localhost:8000
```

El ZIP debe contener la misma estructura de carpetas:
```
lecturas.zip
└── Descriptivo/
    ├── archivo1.txt
    └── archivo2.txt
```

## Salida esperada

```
  API: http://localhost:8000
  Fuente: ../../virtual-world-reading-ai/readings

  Estado API: ok
  Base de datos: connected

  ⚠  Omitido (tipología no reconocida 'Test'): ...\Test\loren ipsun.txt
  ✓  Importado: [Descriptivo] "Bannos" → ID 15
  ✓  Importado: [Descriptivo] "Temporal Reading 1" → ID 16

==================================================
  Importados: 2  |  Errores/Omitidos: 1
==================================================
```

## Notas

- El script **no verifica duplicados**. Si se ejecuta dos veces, las lecturas se duplicarán.
- Para re-importar limpio: eliminar lecturas duplicadas desde Adminer o resetear la BD con `docker-compose down -v`.
- Las lecturas del seed SQL (`002_seed.sql`) se insertan automáticamente al crear el contenedor. Este script es para importar lecturas **adicionales** desde archivos `.txt`.
