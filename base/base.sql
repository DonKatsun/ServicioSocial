CREATE TABLE estado (
    id SERIAL PRIMARY KEY,
    estado VARCHAR(20) NOT NULL
);

CREATE TABLE tipo (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    activo BOOLEAN NOT NULL
);

CREATE TABLE rol (
    id SERIAL PRIMARY KEY,
    rol VARCHAR(50) NOT NULL
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL,
    contrasenia TEXT NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellidop VARCHAR(50) NOT NULL,
    apellidom VARCHAR(50),
    rol INTEGER REFERENCES rol(id)
);

CREATE TABLE secretaria (
    id SERIAL PRIMARY KEY,
    secretaria VARCHAR(100) NOT NULL
);

CREATE TABLE dependencia (
    id SERIAL PRIMARY KEY,
    dependencia VARCHAR(100) NOT NULL,
    secretaria INTEGER REFERENCES secretaria(id)
);

CREATE TABLE universidad (
    id SERIAL PRIMARY KEY,
    universidad VARCHAR(100) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE plantel (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(250),
    universidad INTEGER REFERENCES universidad(id),
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE validador (
    id INTEGER PRIMARY KEY,
    dependencia INTEGER REFERENCES dependencia(id)
);

CREATE TABLE alumno (
    id INTEGER PRIMARY KEY,
    curp VARCHAR(100),
    carrera VARCHAR(100),
    plantel INTEGER REFERENCES plantel(id),
    matricula VARCHAR(100)
);

CREATE TABLE proyectos (
    id SERIAL PRIMARY KEY,
    nombre_proyecto TEXT,
    activo BOOLEAN
);

CREATE TABLE solicitud (
    id SERIAL PRIMARY KEY,
    dependencia INTEGER REFERENCES dependencia(id),
    alumno INTEGER REFERENCES usuarios(id),
    validador INTEGER REFERENCES validador(id),
    estado INTEGER REFERENCES estado(id),
    tipo INTEGER REFERENCES tipo(id),
    anexo TEXT,
    liberacion TEXT,
    fechaliberacion DATE,
    fechasolicitud DATE,
    firma TEXT,
    horas INTEGER,
    carta_aceptacion TEXT,
    acceso_alumno BOOLEAN DEFAULT FALSE,
    proyecto INTEGER REFERENCES proyectos(id)
);

CREATE TABLE reporte (
    id SERIAL PRIMARY KEY,
    solicitud INTEGER REFERENCES solicitud(id),
    archivoreporte TEXT,
    horas INTEGER,
    estado INTEGER REFERENCES estado(id)
);

CREATE TABLE anexos (
    id SERIAL PRIMARY KEY,
    descripcion TEXT,
    anexo TEXT
);

CREATE OR REPLACE FUNCTION calcular_sha256()
RETURNS TRIGGER AS $$
BEGIN
    NEW.sha := encode(digest(CAST(NEW.id AS TEXT), 'sha256'), 'hex');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER solicitud_calcula_sha256
BEFORE INSERT ON solicitud
FOR EACH ROW
EXECUTE FUNCTION calcular_sha256();
