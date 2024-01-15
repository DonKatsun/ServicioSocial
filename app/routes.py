from flask import render_template, jsonify, request
from app import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc,or_,func,case,literal_column
from sqlalchemy.orm import joinedload
from functools import wraps
import jwt
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import base64
import secrets
import string
from sqlalchemy import exc
from app.models import *

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route('/login', methods=['POST'])
def login():
    # Lógica de autenticación del usuario
    data = request.get_json()
    if 'usuario' not in data or 'contrasenia' not in data:
        return jsonify({'error': 'Se requieren campos de usuario y contraseña'}), 400
    # Si la autenticación es exitosa, genera un token JWT con información adicional
    usuario_input = data['usuario']
    contrasenia_input = data['contrasenia']
    #usuarioAuth = usuarios.query.filter_by(usuario=usuario_input, contrasenia=contrasenia_input).join(rol).first()
    usuarioAuth = (
        db.session.query(usuarios)
        .filter_by(usuario=usuario_input, contrasenia=contrasenia_input)
        .join(rol, usuarios.rol == rol.id)
        .first()
    )
    if usuarioAuth:
        rolUsuario = rol.query.filter_by(id=usuarioAuth.rol).first()
        payload = {
            'nombre': f"{usuarioAuth.nombre} {usuarioAuth.apellidop} {usuarioAuth.apellidom}",
            'exp': datetime.utcnow() + timedelta(hours=2),  # Tiempo de expiración del token
            'rol': rolUsuario.rol,
            'id': usuarioAuth.id
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

        # Incluye el token en la respuesta JSON
        response = jsonify({'token': token, 'payload':payload})
        response.headers.add('Access-Control-Allow-Origin', '*')  # Esto puede ser necesario para que acceda el publico
    else:
        response = "Credenciales incorrectas"
    
    return response

@app.route('/')
def index():
    #usuarios = Usuario.query.all()
    #return render_template('index.html', usuarios=usuarios)
    usuarioss = usuarios.query.all()
    for usuario in usuarioss:
        print(f"ID: {usuario.id}, Usuario: {usuario.usuario}, Nombre: {usuario.nombre}")
    print(f"Valor de SECRET_KEY: {app.config['SECRET_KEY']}")
    return "Log in"

@app.route('/registroAlumno', methods=['POST'])
def registroAlumno():
    data = request.get_json()
    curp_existente = alumno.query.filter_by(curp=data.get('curp')).first()
    usuario_existente = usuarios.query.filter_by(usuario=data.get('usuario')).first()

    if curp_existente:
        return "Error: Ya existe un alumno con este CURP.", 400
    
    if usuario_existente:
        return "Error: Ya existe ese usuario.",400
    
    try:
        # Obtener datos del JSON de la solicitud
        data = request.get_json()

         # Crear nuevo usuario
        nuevo_usuario = usuarios()
        nuevo_usuario.usuario = data.get('usuario')
        nuevo_usuario.contrasenia = data.get('contrasenia')
        nuevo_usuario.nombre = data.get('nombre')
        nuevo_usuario.apellidop = data.get('apellidop')
        nuevo_usuario.apellidom = data.get('apellidom')
        nuevo_usuario.rol = 2

        db.session.add(nuevo_usuario)
        db.session.commit()

        # Crear nuevo alumno asociado al usuario
        nuevo_alumno = alumno()
        nuevo_alumno.id = nuevo_usuario.id
        nuevo_alumno.curp = data.get('curp')
        nuevo_alumno.carrera = data.get('carrera')
        nuevo_alumno.plantel = data.get('plantel')

        # Agregar ambos objetos a la sesión y confirmar la transacción
        db.session.add(nuevo_alumno)
        db.session.commit()

        #Crear carpeta para los archivos del usuario
        ruta_carpeta = f"../archivo/{data.get('curp')}"

        # Verificar si la carpeta padre existe, y si no, crearla
        carpeta_padre = os.path.dirname(ruta_carpeta)
        if not os.path.exists(carpeta_padre):
            os.makedirs(carpeta_padre)
        #Crear la carpeta del alumno
        os.mkdir(ruta_carpeta)
 
        return "Usuario y Alumno creados exitosamente.",201

    except Exception as e:
        # En caso de error, realizar un rollback para deshacer los cambios
        db.session.rollback()
        return f"Error al crear Usuario y Alumno: {str(e)}"

    return "Error de formato en los datos recibidos."

@app.route('/registroValidador', methods=['POST'])
def registroValidador():
    data = request.get_json()
    usuario_existente = usuarios.query.filter_by(usuario=data.get('usuario')).first()

    if usuario_existente:
        return "Error: Ya existe ese usuario.",400
    
    try:
        # Obtener datos del JSON de la solicitud
        data = request.get_json()

         # Crear nuevo usuario
        nuevo_usuario = usuarios()
        nuevo_usuario.usuario = data.get('usuario')
        nuevo_usuario.contrasenia = data.get('contrasenia')
        nuevo_usuario.nombre = data.get('nombre')
        nuevo_usuario.apellidop = data.get('apellidop')
        nuevo_usuario.apellidom = data.get('apellidom')
        nuevo_usuario.rol = 3

        db.session.add(nuevo_usuario)
        db.session.commit()

        # Crear nuevo alumno asociado al usuario
        nuevo_validador = validador()
        nuevo_validador.id = nuevo_usuario.id
        nuevo_validador.dependencia = data.get('dependencia')


        # Agregar ambos objetos a la sesión y confirmar la transacción
        db.session.add(nuevo_validador)
        db.session.commit()

        return "Usuario y Validador creados exitosamente."

    except Exception as e:
        # En caso de error, realizar un rollback para deshacer los cambios
        db.session.rollback()
        return f"Error al crear Usuario y Validadorr: {str(e)}"
    return 0

@app.route('/subirReporte', methods=['POST'])
def subirReporte():

    try:
        #data = request.get_json()
        # Intenta obtener el valor del campo 'JSON' del formulario multipart
        json_data_str = request.values.get('JSON')
        # Si se encuentra el campo 'JSON', convierte su valor a un diccionario
        if json_data_str:
            data = json.loads(json_data_str)
        else:
            # Si no se encuentra el campo 'JSON', intenta obtener datos JSON directamente del cuerpo de la solicitud
            data = request.get_json(force=True)
        # Intenta obtener el ID del alumno y las horas del JSON
        id_alumno = data.get('alumno')
        horas = data.get('horas')

        pdf_file = request.files['pdf']
        todo=request.values
        #id_alumno = request.values.get('alumno')
        #horas = request.values.get('horas')
        print(todo)
        alumnoReq = (
            db.session.query(alumno)
            .filter_by(id=id_alumno)
            .first()
        )
        if not alumnoReq:
            return "No existe el alumno"

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/reportes"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        reporteExist=(
            db.session.query(reporte)
            .filter(reporte.archivoreporte == file_path)
            .first()
        )
        if (reporteExist):
            return "Error: Este reporte ya existe"
        
        # Verificar si la carpeta padre existe, y si no, crearla
        carpeta_padre = os.path.dirname(file_path)
        if not os.path.exists(carpeta_padre):
            os.makedirs(carpeta_padre)
        
        pdf_file.save(f"{ruta_carpeta}//{pdf_file.filename}")

        solicitudReq = (
            db.session.query(solicitud)
            .filter(solicitud.alumno == id_alumno, solicitud.fechaliberacion.is_(None))
            .order_by(solicitud.fechasolicitud)
            .first()
        )

        nuevoReporte = reporte()
        nuevoReporte.archivoreporte = file_path
        nuevoReporte.horas = horas
        nuevoReporte.solicitud = solicitudReq.id
        nuevoReporte.estado = 5

        db.session.add(nuevoReporte)
        db.session.commit()

        return "Reporte creado.", 201
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return f"Error en la base de datos: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/subirCarta', methods=['POST'])
def subirCarta():

    try:
        #data = request.get_json()
        # Intenta obtener el valor del campo 'JSON' del formulario multipart
        json_data_str = request.values.get('JSON')
        # Si se encuentra el campo 'JSON', convierte su valor a un diccionario
        if json_data_str:
            data = json.loads(json_data_str)
        else:
            # Si no se encuentra el campo 'JSON', intenta obtener datos JSON directamente del cuerpo de la solicitud
            data = request.get_json(force=True)
        # Intenta obtener el ID del alumno y las horas del JSON
        id_alumno = data.get('alumno')
        horas = data.get('horas')
        id_dependencia = data.get('dependencia')
        tipo_solicitud = data.get('tipo')
        fecha = data.get('fecha')

        pdf_file = request.files['pdf']
        #id_alumno = request.values.get('alumno')
        #horas = request.values.get('horas')
        alumnoReq = (
            db.session.query(alumno)
            .filter_by(id=id_alumno)
            .first()
        )
        if not alumnoReq:
            return "No existe el alumno"

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/solicitudes"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        solicitudExist=(
            db.session.query(solicitud)
            .filter(solicitud.anexo == file_path)
            .first()
        )
        if (solicitudExist):
            return "Error: Esta solicitud ya existe"
        
        # Verificar si la carpeta padre existe, y si no, crearla
        carpeta_padre = os.path.dirname(file_path)
        if not os.path.exists(carpeta_padre):
            os.makedirs(carpeta_padre)
        
        pdf_file.save(f"{ruta_carpeta}//{pdf_file.filename}")

        nuevaSolicitud = solicitud()
        nuevaSolicitud.alumno=id_alumno
        nuevaSolicitud.anexo=file_path
        nuevaSolicitud.dependencia=id_dependencia
        nuevaSolicitud.estado=5
        nuevaSolicitud.fechasolicitud=fecha
        nuevaSolicitud.horas=horas
        nuevaSolicitud.tipo=tipo_solicitud

        db.session.add(nuevaSolicitud)
        db.session.commit()

        return "Solicitud creada.", 201
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return f"Error en la base de datos: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500
    

@app.route('/consultaSolicitudes', methods=['GET'])
def consultaSolicitudes():
    try:
        #FILTRO {todos,Aceptado,Rechazado,Liberado,Suspendido,Pendiente}
        filtro = request.args.get('filtro')
        limite = request.args.get('limite',10)
        if not(filtro and limite):
            return "Parametros no validos",400
        
        if filtro=='todos':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Aceptado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 1)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Rechazado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 2)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Liberado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 3)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Suspendido':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 4)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Pendiente':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 5)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        else:
            return "Error, filtros validos: todos,Aceptado,Rechazado,Liberado,Suspendido,Pendiente"
        
        
        resultados = solicitudes.all()

        solicitudes_json = [
        {
            "solicitud_id": s.id,
            "nombre": f"{u.nombre} {u.apellidop} {u.apellidom}" if u and u.nombre and u.apellidop and u.apellidom else None,
            "estado": e.estado if e else None,
            "tipo": t.tipo if t else None,
            "pdf": obtener_pdf_base64(s.anexo) if s.anexo else None
        }
        for s, a, u, e, t in resultados
        ]


        return jsonify({"solicitudes": solicitudes_json})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def obtener_pdf_base64(ruta_pdf):

    with open(ruta_pdf, "rb") as file:
        pdf_base64 = base64.b64encode(file.read()).decode('utf-8')

    return pdf_base64


@app.route('/consultaLiberaciones', methods=['GET'])
def consultaLiberaciones():
    try:
        #FILTRO {Liberado,Suspendido, alumno, firma}
        filtro = request.args.get('filtro')
        limite = request.args.get('limite',10)
        alumno_id = request.args.get('alumno',0)
        firma = request.args.get('firma','')
        
        if (not(filtro and limite)):
            return "Parametros no validos",400
        
        elif filtro=='Liberado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 3)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Suspendido':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.estado == 4)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='firma':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(or_(solicitud.estado == 4,solicitud.estado == 3),(solicitud.firma == firma))
            .order_by(solicitud.fechaliberacion)
            .limit(limite)
            )
        elif filtro=='alumno':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(or_(solicitud.estado == 4,solicitud.estado == 3),(solicitud.alumno == alumno_id))
            .order_by(solicitud.fechaliberacion)
            .limit(limite)
            )
        else:
            return "Error de filtros"
        
        
        resultados = solicitudes.all()
        solicitudes_json = [
        {
            "solicitud_id": s.id,
            "nombre": f"{u.nombre} {u.apellidop} {u.apellidom}" if u else None,
            "estado": str(e.estado) if e else None,
            "tipo": str(t.tipo) if t else None,
            "firma": str(s.firma) if s.firma is not None else None,
            "fechaLiberacion": str(s.fechaliberacion) if s.fechaliberacion else None,
            "horas": str(s.horas) if s.horas is not None else None,
            "accesoAlumno": s.acceso_alumno,
            "pdf": obtener_pdf_base64(s.liberacion) if s.liberacion else None
        }
        for s, a, u, e, t in resultados
        ]

        print("hola")
        return jsonify({"solicitudes": solicitudes_json})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def obtener_pdf_base64(ruta_pdf):

    with open(ruta_pdf, "rb") as file:
        pdf_base64 = base64.b64encode(file.read()).decode('utf-8')

    return pdf_base64


@app.route('/consultaAlumno', methods=['GET'])
def consultaAlumno():
    alumno_id = request.args.get('alumno')
    if not alumno_id:   return "Usuario no enviado"

    try:
        solicitudes = (
        db.session.query(
            solicitud,
            alumno,
            usuarios,
            estado,
            tipo,
            func.sum(case((reporte.estado == 1, reporte.horas), else_=0)).label('horas_aprobadas')
        )
        .join(alumno, alumno.id == solicitud.alumno)
        .join(usuarios, alumno.id == usuarios.id)
        .join(estado, estado.id == solicitud.estado)
        .join(tipo, tipo.id == solicitud.tipo)
        .outerjoin(reporte, reporte.solicitud == solicitud.id)
        .filter(solicitud.alumno == alumno_id)
        .group_by(
            solicitud.id,
            alumno.id,
            usuarios.id,
            estado.id,
            tipo.id
        )
    )
        
        resultados = solicitudes.all()
        #if not resultados:   return "No hay resultados"

        solicitudes_json = [
        {
            "solicitud_id": s.id,
            "nombre": f"{u.nombre} {u.apellidop} {u.apellidom}" if u else None,
            "estado": str(e.estado) if e else None,
            "tipo": str(t.tipo) if t else None,
            "firma": str(s.firma) if ((s.firma is not None) and s.acceso_alumno) else None,
            "fechaLiberacion": str(s.fechaliberacion) if s.fechaliberacion else None,
            "horas": str(s.horas) if s.horas is not None else None,
            "accesoAlumno": s.acceso_alumno if s.acceso_alumno is not None else None,
            "horas_abrobadas": sum if sum is not None else 0,
            "pdf_aceptacion": obtener_pdf_base64(s.liberacion) if s.liberacion is not None else None,
            "pdf_liberacion": obtener_pdf_base64(s.carta_aceptacion) if ((s.carta_aceptacion is not None) and s.acceso_alumno) else None
        }
        for s, a, u, e, t, sum in resultados
        ]

        return jsonify({"solicitudes": solicitudes_json})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/consultaReportesAlumno', methods=['GET'])
def consultaReportesAlumno():
    alumno_id = request.args.get('alumno')
    if not alumno_id:   return "Usuario no enviado"

    try:
        solicitudes = (
        db.session.query(
            solicitud,
            alumno,
            usuarios,
            estado,
            tipo,
            reporte
        )
        .join(alumno, alumno.id == solicitud.alumno)
        .join(usuarios, alumno.id == usuarios.id)
        .join(reporte, reporte.solicitud == solicitud.id)
        .join(estado, estado.id == reporte.estado)
        .join(tipo, tipo.id == solicitud.tipo)
        .filter(solicitud.alumno == alumno_id)

    )
        
        resultados = solicitudes.all()
        if not resultados:   return "No hay resultados"

        solicitudes_json = [
        {
            "reporte_id": r.id,
            "nombre": f"{u.nombre} {u.apellidop} {u.apellidom}" if u else None,
            "estado": str(e.estado) if e else None,
            "horas": r.horas if r.horas is not None else None,
            "pdf_reporte": obtener_pdf_base64(r.archivoreporte) if r.archivoreporte is not None else None,
        }
        for s, a, u, e, t, r in resultados
        ]

        return jsonify({"solicitudes": solicitudes_json})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/AceptarRechazarSolicitud', methods=['PATCH'])
def AceptarRechazarSolicitud():
    try:
        json_data_str = request.values.get('JSON')
        # Si se encuentra el campo 'JSON', convierte su valor a un diccionario
        if json_data_str:
            data = json.loads(json_data_str)
        else:
            # Si no se encuentra el campo 'JSON', intenta obtener datos JSON directamente del cuerpo de la solicitud
            data = request.get_json(force=True)
        # Intenta obtener el ID del alumno y las horas del JSON
        #{"solicitud":"1","estatus":"Rechazado","validador":"8"}
        solicitud_id = data.get('solicitud')
        estatus = data.get('estatus')
        validador = data.get('validador')
        #estatus {Aceptado,Rechazado,Liberado,Suspendido,Pendiente}
        
        solicitudExist=(
            db.session.query(solicitud)
            .filter(solicitud.id == solicitud_id)
            .first()
        )

        alumnoReq = (
            db.session.query(alumno)
            .filter_by(id=solicitudExist.alumno)
            .first()
        )

        solicitudExist.validador = validador

        if not solicitudExist:
            return "Solicitud no encontrada",400
        
        if estatus == "Rechazado":
            estatus = 2
            solicitudExist.estado = estatus
            db.session.commit()
            return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} rechazada correctamente"}), 200
        
        if estatus != "Aceptado":
            return jsonify({"mensaje": f"Estatus no valido"}), 200
        
        pdf_file = request.files['pdf']

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/cartaAceptacion"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        solicitudExiste=(
            db.session.query(solicitud)
            .filter(solicitud.carta_aceptacion == file_path)
            .first()
        )
        if (solicitudExiste):
            return "Error: Esta solicitud ya existe"
        
        # Verificar si la carpeta padre existe, y si no, crearla
        carpeta_padre = os.path.dirname(file_path)
        if not os.path.exists(carpeta_padre):
            os.makedirs(carpeta_padre)
        
        pdf_file.save(f"{ruta_carpeta}//{pdf_file.filename}")

        solicitudExist.estado = 1
        solicitudExist.carta_aceptacion = file_path
        db.session.commit()

        return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} aceptada correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/AceptarRechazarLiberacion', methods=['PATCH'])
def AceptarRechazarLiberacion():
    try:
        json_data_str = request.values.get('JSON')
        # Si se encuentra el campo 'JSON', convierte su valor a un diccionario
        if json_data_str:
            data = json.loads(json_data_str)
        else:
            # Si no se encuentra el campo 'JSON', intenta obtener datos JSON directamente del cuerpo de la solicitud
            data = request.get_json(force=True)
        # Intenta obtener el ID del alumno y las horas del JSON
        #{"solicitud":"1","estatus":"Rechazado","validador":"8"}
        solicitud_id = data.get('solicitud')
        estatus = data.get('estatus')
        validador = data.get('validador')
        #estatus {Aceptado,Rechazado,Liberado,Suspendido,Pendiente}
        
        solicitudExist=(
            db.session.query(solicitud)
            .filter(solicitud.id == solicitud_id)
            .first()
        )

        alumnoReq = (
            db.session.query(alumno)
            .filter_by(id=solicitudExist.alumno)
            .first()
        )

        solicitudExist.validador = validador

        if not solicitudExist:
            return "Solicitud no encontrada",400
        
        if estatus == "Rechazado":
            estatus = 4
            solicitudExist.estado = estatus
            db.session.commit()
            return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} suspendida correctamente"}), 200
        
        if estatus != "Aceptado":
            return jsonify({"mensaje": f"Estatus no valido"}), 200
        
        pdf_file = request.files['pdf']

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/cartaLiberacion"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        solicitudExiste=(
            db.session.query(solicitud)
            .filter(solicitud.liberacion == file_path)
            .first()
        )
        if (solicitudExiste):
            return "Error: Esta solicitud ya existe"
        
        # Verificar si la carpeta padre existe, y si no, crearla
        carpeta_padre = os.path.dirname(file_path)
        if not os.path.exists(carpeta_padre):
            os.makedirs(carpeta_padre)
        
        pdf_file.save(f"{ruta_carpeta}//{pdf_file.filename}")

        fecha = datetime.now()
        # Formatear la fecha en formato SQL (YYYY-MM-DD)
        fecha = fecha.strftime('%Y-%m-%d')
        identificador = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        firma = f"{alumnoReq.curp}_{solicitudExist.id}{identificador}"

        solicitudExist.estado = 3
        solicitudExist.liberacion = file_path
        solicitudExist.fechaliberacion = fecha
        solicitudExist.firma = firma

        db.session.commit()

        return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} liberada correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500