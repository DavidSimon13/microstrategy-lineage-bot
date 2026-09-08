# Metodología de Lineage MicroStrategy

## Objetivo

Identificar, a partir de un objeto de MicroStrategy, todas sus dependencias relevantes hasta llegar a las tablas físicas relacionales utilizadas.

El objetivo final es determinar el conjunto mínimo de tablas que deben considerarse para una migración hacia AWS.

---

## Fuente de información

La fuente principal para el análisis es Platform Analytics.

Cada dataset contiene relaciones entre:

- Object Name
- Object GUID
- Object Type DESC
- Component Object Name
- Component Object GUID
- Component Object Type DESC
- Project

La identidad principal de un objeto será siempre su GUID.

---

## Niveles arquitectónicos

### N6 - Presentación / Consumo

- Dashboard
- Document

### N5 - Ejecución / Dataset

- Grid Report
- Graph Report
- Grid and Graph Report
- SQL Report
- OLAP Cube
- Data Import Cube
- Managed Grid Report
- Managed Data Import Cube
- Transaction Services Report

### N4 - Lógica Analítica

- Metric
- Managed Metric
- Filter
- User Filter
- Custom Group
- Consolidation
- Derived Element
- Managed Derived Element
- Metric Subtotal
- Attribute Element Prompt
- Object Prompt
- Value Prompt
- Prompt
- Template

### N3 - Modelo Semántico

- Attribute
- Managed Attribute
- Fact
- Transformation
- Attribute Transformation

### N2 - Mapeo Lógico

- Logical Table
- Partition Logical Table

Objetos terminales frecuentes:

- Managed Attribute Form
- Attribute Form Category

### N1 - Modelo Físico

- Database Table
- Managed Database Table

Objetos terminales:

- Column
- Managed Column

---

## Dirección principal del lineage

Platform Analytics se interpreta como un grafo de dependencias.

La relación principal es:

Object GUID
→
Component Object GUID

Un objeto puede aparecer como padre en una relación y como componente en otra.

Por lo tanto, el lineage no debe tratarse como un árbol rígido.

---

## Reglas de navegación

1. Utilizar GUID como identificador principal.

2. Recorrer todos los componentes descendientes del objeto inicial.

3. Permitir relaciones entre objetos del mismo nivel.

Ejemplos:

N5 → N5

N4 → N4

N3 → N3

N2 → N2

N1 → N1

4. Permitir saltos de nivel.

Ejemplo:

N3 → N1

5. Evitar ciclos manteniendo un registro de:

- GUID visitados
- relaciones visitadas

6. Continuar el recorrido hasta localizar:

- Logical Table
- Partition Logical Table
- Database Table
- Managed Database Table

7. Column y Managed Column se utilizan como validación técnica, pero no forman parte del inventario de tablas a migrar.

---

## Regla especial para Logical Tables

Cuando se llega a una Logical Table, el objetivo principal es localizar su tabla física:

Logical Table
→
Database Table

o

Logical Table
→
Managed Database Table

No se debe expandir indiscriminadamente desde una Logical Table hacia todos sus Attributes y Facts porque esto puede inflar artificialmente el scope de migración.

---

## Clasificación para migración

Cada tabla física encontrada podrá clasificarse como:

### MIGRATE

Tabla física confirmada como parte del consumo efectivo del objeto.

### VALIDATE_SQL

Tabla alcanzada mediante relaciones semánticas indirectas y que requiere validar el SQL real generado por MicroStrategy antes de migrarla.

### AUXILIARY

Tabla técnica o auxiliar que aparece en el lineage pero no se ha confirmado como fuente principal.

### NOT_PHYSICAL

Objeto de metadata que no representa una tabla relacional.

### TERMINAL_COLUMN

Column o Managed Column utilizada únicamente como validación técnica.

---

## Salida esperada

Para cada objeto analizado se debe generar:

### Información del objeto

- Proyecto
- Object Name
- Object GUID
- Object Type
- Nivel arquitectónico
- Object Location

### Lineage

- Componentes directos
- Metrics
- Filters
- Attributes
- Facts
- Logical Tables

### Tablas físicas

- Physical Table Name
- Physical Table GUID
- Estado de migración

### Resumen AWS

- Cantidad de tablas físicas únicas
- Tablas MIGRATE
- Tablas VALIDATE_SQL

---

## Regla de deduplicación

Una misma tabla física puede ser alcanzada por diferentes ramas del lineage.

El resultado final deberá contener cada tabla física una sola vez.

La deduplicación deberá realizarse principalmente por GUID.

---

## Principio fundamental

Lineage técnico != Scope de migración AWS

El lineage técnico conserva todas las relaciones necesarias para explicar cómo se llega a una tabla.

El scope AWS contiene únicamente las tablas físicas únicas que realmente deben ser consideradas para la migración.
