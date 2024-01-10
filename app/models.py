from app import db

class estado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(20), nullable=False)

    def __init__(self, estado):
        self.estado = estado

class tipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    activo = db.Column(db.Boolean, nullable=False)

    def __init__(self, tipo, activo):
        self.tipo = tipo
        self.activo = activo

class rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rol = db.Column(db.String(50), nullable=False)

    def __init__(self, rol):
        self.rol = rol

class usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), nullable=False)
    contrasenia = db.Column(db.Text, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellidop = db.Column(db.String(50), nullable=False)
    apellidom = db.Column(db.String(50))
    rol = db.Column(db.Integer, db.ForeignKey('rol.id'))

'''    def __init__(self, usuario, contrasenia, nombre, apellidop, apellidom, rol):
        self.usuario = usuario
        self.contrasenia = contrasenia
        self.nombre = nombre
        self.apellidop = apellidop
        self.apellidom = apellidom
        self.rol = rol'''

class secretaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    secretaria = db.Column(db.String(100), nullable=False)

    def __init__(self, secretaria):
        self.secretaria = secretaria

class dependencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dependencia = db.Column(db.String(100), nullable=False)
    secretaria = db.Column(db.Integer, db.ForeignKey('secretaria.id'))


class universidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    universidad = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, universidad, activo=True):
        self.universidad = universidad
        self.activo = activo

class plantel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(250))
    universidad = db.Column(db.Integer, db.ForeignKey('universidad.id'))
    activo = db.Column(db.Boolean, default=True)

    def __init__(self, nombre, direccion, universidad, activo=True):
        self.nombre = nombre
        self.direccion = direccion
        self.universidad = universidad
        self.activo = activo

class validador(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    dependencia = db.Column(db.Integer, db.ForeignKey('dependencia.id'))


class alumno(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    curp = db.Column(db.String(100))
    carrera = db.Column(db.String(100))
    plantel = db.Column(db.Integer, db.ForeignKey('plantel.id'))

'''    def __init__(self, curp, carrera, plantel):
        self.curp = curp
        self.carrera = carrera
        self.plantel = plantel'''

class solicitud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dependencia = db.Column(db.Integer, db.ForeignKey('dependencia.id'))
    alumno = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    validador = db.Column(db.Integer, db.ForeignKey('validador.id'))
    estado = db.Column(db.Integer, db.ForeignKey('estado.id'))
    tipo = db.Column(db.Integer, db.ForeignKey('tipo.id'))
    anexo = db.Column(db.Text)
    liberacion = db.Column(db.Text)
    fechaLiberacion = db.Column(db.Date)
    fechaSolicitud = db.Column(db.Date)
    firma = db.Column(db.Text)

    def __init__(self, dependencia, alumno, validador, estado, tipo, anexo, liberacion, fechaLiberacion, fechaSolicitud, firma):
        self.dependencia = dependencia
        self.alumno = alumno
        self.validador = validador
        self.estado = estado
        self.tipo = tipo
        self.anexo = anexo
        self.liberacion = liberacion
        self.fechaLiberacion = fechaLiberacion
        self.fechaSolicitud = fechaSolicitud
        self.firma = firma

class reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitud = db.Column(db.Integer, db.ForeignKey('solicitud.id'))
    archivoReporte = db.Column(db.Text)
    horas = db.Column(db.Integer)
    estado = db.Column(db.Integer, db.ForeignKey('estado.id'))

    def __init__(self, solicitud, archivoReporte, horas, estado):
        self.solicitud = solicitud
        self.archivoReporte = archivoReporte
        self.horas = horas
        self.estado = estado
