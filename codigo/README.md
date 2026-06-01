# botstore
telegram bot store

CREATE DATABASE IF NOT EXISTS bot_telegram;
USE bot_telegram;

-- ==========================================
-- TABLA: CLAVES DE ACCESO
-- ==========================================

CREATE TABLE claves_acceso (
id INT NOT NULL AUTO_INCREMENT,
clave VARCHAR(50) NOT NULL,
fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (id),
UNIQUE KEY clave (clave)
);

-- ==========================================
-- TABLA: USUARIOS AUTORIZADOS
-- ==========================================

CREATE TABLE usuarios_autorizados (
user_id BIGINT NOT NULL,
fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
estado VARCHAR(20) DEFAULT 'activo',
creditos INT DEFAULT 0,
PRIMARY KEY (user_id)
);

-- ==========================================
-- TABLA: CONFIGURACIÓN DEL SISTEMA
-- ==========================================

CREATE TABLE configuracion_sistema (
id INT NOT NULL AUTO_INCREMENT,
parametro VARCHAR(50) NOT NULL,
valor VARCHAR(255) NOT NULL,
descripcion TEXT,
PRIMARY KEY (id),
UNIQUE KEY parametro (parametro)
);

-- ==========================================
-- TABLA: CATÁLOGO DE SERVICIOS
-- ==========================================

CREATE TABLE catalogo_servicios (
codigo_servicio VARCHAR(50) NOT NULL,
nombre_mostrar VARCHAR(100) NOT NULL,
descripcion TEXT,
precio_estimado DECIMAL(10,2) DEFAULT 0.00,
PRIMARY KEY (codigo_servicio)
);

-- ==========================================
-- TABLA: INVENTARIO DE CUENTAS
-- ==========================================

CREATE TABLE inventario_cuentas (
id INT NOT NULL AUTO_INCREMENT,
codigo_servicio VARCHAR(50) NOT NULL,
credenciales TEXT NOT NULL,
estado VARCHAR(20) DEFAULT 'disponible',
fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (id),
FOREIGN KEY (codigo_servicio)
REFERENCES catalogo_servicios(codigo_servicio)
ON DELETE CASCADE
);

-- ==========================================
-- TABLA: COMBOS
-- ==========================================

CREATE TABLE combos (
id INT NOT NULL AUTO_INCREMENT,
servicio VARCHAR(50) NOT NULL,
cuenta TEXT NOT NULL,
estado VARCHAR(20) DEFAULT 'disponible',
fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (id)
);

-- ==========================================
-- TABLA: REGISTRO DE ENTREGAS
-- ==========================================

CREATE TABLE registro_entregas (
id INT NOT NULL AUTO_INCREMENT,
user_id BIGINT NOT NULL,
combo_id INT NOT NULL,
fecha_entrega TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (id),
FOREIGN KEY (user_id)
REFERENCES usuarios_autorizados(user_id)
ON DELETE CASCADE,
FOREIGN KEY (combo_id)
REFERENCES combos(id)
ON DELETE CASCADE
);

-- ==========================================
-- TABLA: LOGS
-- ==========================================

CREATE TABLE logs (
id INT NOT NULL AUTO_INCREMENT,
user_id BIGINT,
mensaje TEXT,
fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (id)
);

-- ==========================================
-- DATOS DE PRUEBA
-- ==========================================

INSERT INTO configuracion_sistema
(parametro, valor, descripcion)
VALUES
('precio_credito','10','Precio por crédito'),
('modo_mantenimiento','0','Modo mantenimiento');

INSERT INTO claves_acceso (clave)
VALUES
('DEMO-KEY-001'),
('DEMO-KEY-002');

INSERT INTO usuarios_autorizados
(user_id, creditos)
VALUES
(123456789,100);

INSERT INTO catalogo_servicios
(codigo_servicio,nombre_mostrar,precio_estimado)
VALUES
('NETFLIX','Netflix Premium',20.00),
('SPOTIFY','Spotify Premium',15.00);

INSERT INTO inventario_cuentas
(codigo_servicio,credenciales)
VALUES
('NETFLIX','[correo@demo.com](mailto:correo@demo.com):123456');

INSERT INTO combos
(servicio,cuenta)
VALUES
('NETFLIX','[correo@demo.com](mailto:correo@demo.com):123456');
