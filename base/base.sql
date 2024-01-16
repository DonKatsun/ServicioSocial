-- Database: servicioSocial
--DROP DATABASE IF EXISTS "servicioSocial";

--CREATE DATABASE "servicioSocial"
--    WITH
--    OWNER = postgres
--    ENCODING = 'UTF8'
--    LC_COLLATE = 'Spanish_Mexico.1252'
--    LC_CTYPE = 'Spanish_Mexico.1252'
--    LOCALE_PROVIDER = 'libc'
--    TABLESPACE = pg_default
--    CONNECTION LIMIT = -1
--    IS_TEMPLATE = False;
--CREATE TYPE estado AS ENUM ('Aceptado', 'Rechazado', 'Liberado', 'Suspendido','Pendiente');
--CREATE TYPE tipo AS ENUM ('Servivicio social', 'Prácticas profecionales');
CREATE TABLE estado(
	id SERIAL PRIMARY KEY,
	estado VARCHAR(20)
);

CREATE TABLE tipo (
    id SERIAL PRIMARY KEY,
	tipo varchar(50) NOT NULL,
	activo bool not NULL
);

CREATE TABLE rol(
	id SERIAL PRIMARY KEY,
	rol VARCHAR(50)
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
	usuario varchar(50) NOT NULL,
	contrasenia text NOT NULL,
    nombre VARCHAR(50) NOT NULL,
	apellidoP VARCHAR(50) NOT NULL,
	apellidoM VARCHAR(50),
	rol INTEGER REFERENCES rol(id)
);

CREATE TABLE secretaria (
    id SERIAL PRIMARY KEY,
	secretaria varchar(100) NOT NULL
);

CREATE TABLE dependencia (
    id SERIAL PRIMARY KEY,
	dependencia varchar(100) NOT NULL,
	secretaria INTEGER REFERENCES secretaria(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE universidad (
    id SERIAL PRIMARY KEY,
	universidad varchar(100) NOT NULL, 
	activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE plantel (
    id SERIAL PRIMARY KEY,
	nombre varchar(100) NOT NULL,
	direccion varchar(250),
	universidad INTEGER REFERENCES universidad(id) ON DELETE SET NULL ON UPDATE CASCADE,
	activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE validador (
    id INTEGER PRIMARY KEY REFERENCES usuarios(id),
	dependencia INTEGER REFERENCES dependencia(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE alumno (
    id INTEGER PRIMARY KEY REFERENCES usuarios(id),
	curp varchar(100),
	carrera varchar(100),
	plantel INTEGER REFERENCES plantel(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE solicitud (
    id SERIAL PRIMARY KEY,
	dependencia INTEGER REFERENCES dependencia(id) ON DELETE SET NULL ON UPDATE CASCADE,
	alumno INTEGER REFERENCES usuarios(id),
	validador INTEGER REFERENCES validador(id),
	estado INTEGER REFERENCES estado(id),
	tipo INTEGER REFERENCES tipo(id),
	anexo text,
	liberacion text,
	fechaLiberacion date,
	fechaSolicitud date,
	firma text,
	horas INTEGER,
	carta_aceptacion TEXT,
	acceso_alummno BOOLEAN DEFAULT FALSE
);

CREATE TABLE reporte (
    id SERIAL,
	solicitud INTEGER REFERENCES solicitud(id) ON UPDATE CASCADE,
	archivoReporte text,
	horas INTEGER,
	estado INTEGER REFERENCES estado(id),
	PRIMARY KEY (id,solicitud)
);