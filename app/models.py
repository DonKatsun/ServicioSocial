from app import db

class estado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(20), nullable=False)


class tipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    activo = db.Column(db.Boolean, nullable=False)


class rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rol = db.Column(db.String(50), nullable=False)


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


class dependencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dependencia = db.Column(db.String(100), nullable=False)
    secretaria = db.Column(db.Integer, db.ForeignKey('secretaria.id'))


class universidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    universidad = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)


class plantel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(250))
    universidad = db.Column(db.Integer, db.ForeignKey('universidad.id'))
    activo = db.Column(db.Boolean, default=True)


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
    fechaliberacion = db.Column(db.Date)
    fechasolicitud = db.Column(db.Date)
    firma = db.Column(db.Text)
    horas = db.Column(db.Integer)
    carta_aceptacion =db.Column(db.Text)
    acceso_alumno = db.Column(db.Boolean, default=False)


class reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitud = db.Column(db.Integer, db.ForeignKey('solicitud.id'))
    archivoreporte = db.Column(db.Text)
    horas = db.Column(db.Integer)
    estado = db.Column(db.Integer, db.ForeignKey('estado.id'))

class anexos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text)
    anexo = db.Column(db.Text)