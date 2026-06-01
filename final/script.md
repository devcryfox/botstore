-- 1. CREACIÓN DE LA BASE DE DATOS
CREATE DATABASE IF NOT EXISTS railway;
USE railway;

-- ========================================================
-- 2. CREACIÓN DE LAS 5 TABLAS DEL SISTEMA
-- ========================================================

-- TABLA 1: Configuración global (Precios dinámicos, etc.)
CREATE TABLE IF NOT EXISTS configuracion_sistema (
    parametro VARCHAR(100) PRIMARY KEY,
    valor VARCHAR(100) NOT NULL
);

-- TABLA 2: Llaves/Keys de registro generadas por el Admin
CREATE TABLE IF NOT EXISTS claves_acceso (
    clave VARCHAR(100) PRIMARY KEY,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 3: Clientes/Usuarios autorizados y su saldo disponible
CREATE TABLE IF NOT EXISTS usuarios_autorizados (
    user_id BIGINT PRIMARY KEY,
    creditos INT DEFAULT 0,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 4: Inventario de cuentas disponibles para entrega automática
CREATE TABLE IF NOT EXISTS cuentas_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_producto VARCHAR(100) NOT NULL, -- Ej. 'Netflix', 'Spotify', etc.
    datos_cuenta TEXT NOT NULL,          -- Formato correo:contraseña
    estado VARCHAR(20) DEFAULT 'DISPONIBLE', -- DISPONIBLE o VENDIDA
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 5: Registro/Historial de ventas realizadas por el bot
CREATE TABLE IF NOT EXISTS historial_ventas (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    id_cuenta INT,
    precio_pagado INT NOT NULL,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuarios_autorizados(user_id) ON DELETE CASCADE,
    FOREIGN KEY (id_cuenta) REFERENCES cuentas_inventario(id) ON DELETE CASCADE
);

-- ========================================================
-- 3. INSERCIÓN DE DATOS DE PRUEBA (MOCK DATA)
-- ========================================================

INSERT INTO configuracion_sistema (parametro, valor) VALUES 
('precio_cuenta', '20');

INSERT INTO claves_acceso (clave) VALUES 
('KEY-FOX-99A8'),
('KEY-FOX-44B2'),
('KEY-FOX-1234');

INSERT INTO usuarios_autorizados (user_id, creditos) VALUES 
(123456789, 100), -- Usuario de prueba con saldo
(987654321, 0);   -- Usuario nuevo sin saldo

INSERT INTO cuentas_inventario (tipo_producto, datos_cuenta, estado) VALUES 
('Premium', 'premiumuser1@gmail.com:foxpass123', 'DISPONIBLE'),
('Premium', 'premiumuser2@gmail.com:foxpass456', 'DISPONIBLE'),
('Premium', 'vieja_cuenta@gmail.com:passold', 'VENDIDA');

INSERT INTO historial_ventas (user_id, id_cuenta, precio_pagado) VALUES 
(123456789, 3, 20); -- Registro de que el usuario 123456789 ya compró una cuenta antes