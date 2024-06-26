from urllib import response
from flask import render_template, jsonify, request, send_file
import qrcode
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
from io import BytesIO
import base64
import secrets
import string
from sqlalchemy import exc
from app.models import *
import hashlib
from urllib.parse import quote
from functools import wraps
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token faltante'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data  # Aquí puedes acceder a la información del usuario del token
        except:
            return jsonify({'error': 'Token inválido'}), 401

        return f(current_user, *args, **kwargs)

    return decorated
@app.route('/login', methods=['POST'])
def login():
    # Lógica de autenticación del usuario
    data = request.get_json()
    if 'usuario' not in data or 'contrasenia' not in data:
        return jsonify({'error': 'Se requieren campos de usuario y contraseña'}), 400
    # Si la autenticación es exitosa, genera un token JWT con información adicional
    usuario_input = data['usuario']
    contrasenia_input = data['contrasenia']
    print(usuario_input, contrasenia_input)
    #print(usuarioAuth)
    user = (
        db.session.query(usuarios)
        .filter_by(usuario=usuario_input, contrasenia=contrasenia_input)
        .first()
    )
    print(user)
    if not user:
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    if user.rol == 2:
        usuarioAuth = (
            db.session.query(usuarios,universidad,plantel)
            .filter_by(usuario=usuario_input, contrasenia=contrasenia_input)
            .outerjoin(rol, usuarios.rol == rol.id)
            .outerjoin(alumno, usuarios.id == alumno.id)
            .outerjoin(plantel, alumno.plantel == plantel.id)
            .outerjoin(universidad, universidad.id == plantel.universidad)
            .first()
        )
    else:
        usuarioAuth = (
            db.session.query(usuarios)
            .filter_by(usuario=usuario_input, contrasenia=contrasenia_input)
            .outerjoin(rol, usuarios.rol == rol.id)
            .outerjoin(alumno, usuarios.id == alumno.id)
            .all()
        )

    #print(usuarioAuth)
    if usuarioAuth:
        rolUsuario = rol.query.filter_by(id=user.rol).first()
        #print(rolUsuario.id)
        uni= None if rolUsuario.id != 2 else usuarioAuth[1].universidad
        plante = None if rolUsuario.id != 2 else usuarioAuth[2].nombre
        payload = {
            'nombre': f"{usuarioAuth[0].nombre} {usuarioAuth[0].apellidop} {usuarioAuth[0].apellidom}",
            'exp': datetime.utcnow() + timedelta(hours=2),  # Tiempo de expiración del token
            'rol': rolUsuario.rol,
            'id': usuarioAuth[0].id,
            'universidad': uni,
            'plantel': plante,
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

        # Incluye el token en la respuesta JSON
        response = jsonify({'token': token, 'nombre': payload['nombre'],
                            'exp': payload['exp'],'rol': payload['rol'],'id': payload['id'],'universidad': payload['universidad'],'plantel': payload['plantel']})
        response.headers.add('Access-Control-Allow-Origin', '*')  # Esto puede ser necesario para que acceda el publico
    else:
        response = "Credenciales incorrectas",400
    
    return response

@app.route('/')
def index():
    return "Log in"

@app.route('/registroAlumno', methods=['POST'])
@token_required
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
        nuevo_alumno.matricula = data.get('matricula')

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
        return f"Error al crear Usuario y Alumno: {str(e)}",400

    return "Error de formato en los datos recibidos."

@app.route('/registroValidador', methods=['POST'])
@token_required
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
        return f"Error al crear Usuario y Validadorr: {str(e)}",400
    return 0

@app.route('/subirReporte', methods=['POST'])
@token_required
def subirReporte():
    print(request.values)
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
        #print(todo)
        alumnoReq = (
            db.session.query(alumno)
            .filter_by(id=id_alumno)
            .first()
        )
        if not alumnoReq:
            return "No existe el alumno",400

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/reportes"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        reporteExist=(
            db.session.query(reporte)
            .filter(reporte.archivoreporte == file_path)
            .first()
        )
        if (reporteExist):
            return "Error: Este reporte ya existe",400
        
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
        return f"Error en la base de datos: {str(e)}", 400
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/subirCarta', methods=['POST'])
@token_required
def subirCarta():

    try:
        print(request.values)
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
        print(pdf_file)
        #id_alumno = request.values.get('alumno')
        #horas = request.values.get('horas')
        alumnoReq = (
            db.session.query(alumno)
            .filter_by(id=id_alumno)
            .first()
        )
        if not alumnoReq:
            return "No existe el alumno",400

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/solicitudes"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        solicitudExist=(
            db.session.query(solicitud)
            .filter(solicitud.anexo == file_path)
            .first()
        )
        if (solicitudExist):
            return "Error: Esta solicitud ya existe",400
        
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
@token_required
def consultaSolicitudes():
    try:
        #FILTRO {todos,Aceptado,Rechazado,Liberado,Suspendido,Pendiente}
        filtro = request.args.get('filtro')
        limite = request.args.get('limite',10)
        if not(filtro and limite):
            return "Parametros no validos",400
        
        if filtro=='todos':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, plantel.id == alumno.plantel)
            .join(universidad, universidad.id == plantel.universidad)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Aceptado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, plantel.id == alumno.plantel)
            .join(universidad, universidad.id == plantel.universidad)
            .filter(solicitud.estado == 1)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Rechazado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, plantel.id == alumno.plantel)
            .join(universidad, universidad.id == plantel.universidad)
            .filter(solicitud.estado == 2)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Liberado':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, plantel.id == alumno.plantel)
            .join(universidad, universidad.id == plantel.universidad)
            .filter(solicitud.estado == 3)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Suspendido':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, plantel.id == alumno.plantel)
            .join(universidad, universidad.id == plantel.universidad)
            .filter(solicitud.estado == 4)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Pendiente':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, plantel.id == alumno.plantel)
            .join(universidad, universidad.id == plantel.universidad)
            .filter(solicitud.estado == 5)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        else:
            return "Error, filtros validos: todos,Aceptado,Rechazado,Liberado,Suspendido,Pendiente",400
        
        
        resultados = solicitudes.all()
        #escuela--fecha
        solicitudes_json = [
        {
            "solicitud_id": s.id,
            "nombre": f"{u.nombre} {u.apellidop} {u.apellidom}" if u and u.nombre and u.apellidop and u.apellidom else None,
            "plantel":p.nombre,
            "universidad":uni.universidad,
            "estado": e.estado if e else None,
            "tipo": t.tipo if t else None,
            "fecha":s.fechasolicitud,
            "pdf": obtener_pdf_base64(s.anexo) if s.anexo else None,
            "pdf_aceptacion": obtener_pdf_base64(s.carta_aceptacion) if s.carta_aceptacion else None,
            
        }
        for s, a, u, e, t, p, uni in resultados
        ]


        return jsonify({"solicitudes": solicitudes_json})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def obtener_pdf_base64(ruta_pdf):

    with open(ruta_pdf, "rb") as file:
        pdf_base64 = base64.b64encode(file.read()).decode('utf-8')

    return pdf_base64


@app.route('/consultaLiberaciones', methods=['GET'])
@token_required
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
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, alumno.plantel == plantel.id)
            .join(universidad, plantel.universidad == universidad.id)
            .filter(solicitud.estado == 3)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='Suspendido':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, alumno.plantel == plantel.id)
            .join(universidad, plantel.universidad == universidad.id)
            .filter(solicitud.estado == 4)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        elif filtro=='firma':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, alumno.plantel == plantel.id)
            .join(universidad, plantel.universidad == universidad.id)
            .filter(or_(solicitud.estado == 4,solicitud.estado == 3),(solicitud.firma == firma))
            .order_by(solicitud.fechaliberacion)
            .limit(limite)
            )
        elif filtro=='alumno':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, alumno.plantel == plantel.id)
            .join(universidad, plantel.universidad == universidad.id)
            .filter(or_(solicitud.estado == 4,solicitud.estado == 3),(solicitud.alumno == alumno_id))
            .order_by(solicitud.fechaliberacion)
            .limit(limite)
            )
        elif filtro=='pendiente':
            solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo,plantel,universidad)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .join(plantel, alumno.plantel == plantel.id)
            .join(universidad, plantel.universidad == universidad.id)
            .filter(solicitud.estado == 6)
            .order_by(solicitud.fechasolicitud)
            .limit(limite)
            )
        else:
            return "Error de filtros",400
        
        
        resultados = solicitudes.all()
        solicitudes_json = [
        {
            "solicitud_id": s.id,
            "nombre": f"{u.nombre} {u.apellidop} {u.apellidom}" if u else None,
            "estado": str(e.estado) if e else None,
            "tipo": str(t.tipo) if t else None,
            "firma": str(s.firma) if s.firma is not None else None,
            "fechaLiberacion": str(s.fechaliberacion) if s.fechaliberacion else None,
            "fechaSolicitud":s.fechasolicitud,
            "horas": str(s.horas) if s.horas is not None else None,
            "accesoAlumno": s.acceso_alumno,
            "plantel":p.nombre,
            "universidad":uni.universidad,
            "pdf": obtener_pdf_base64(s.liberacion) if s.liberacion else None,
            "pdf_liberacion":obtener_pdf_base64(s.liberacion) if s.liberacion else None,
        }
        for s, a, u, e, t, p, uni in resultados
        ]

        return jsonify({"solicitudes": solicitudes_json})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def obtener_pdf_base64(ruta_pdf):

    with open(ruta_pdf, "rb") as file:
        pdf_base64 = base64.b64encode(file.read()).decode('utf-8')

    return pdf_base64


@app.route('/consultaAlumno', methods=['GET'])
@token_required
def consultaAlumno():
    alumno_id = request.args.get('alumno')
    if not alumno_id:   return "Usuario no enviado",400

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
            "pdf_liberacion": obtener_pdf_base64(s.liberacion) if (s.liberacion) and (s.acceso) is not None else None,
            "pdf_aceptacion": obtener_pdf_base64(s.carta_aceptacion) if ((s.carta_aceptacion is not None) and (s.acceso_aceptacion)) else None
        }
        for s, a, u, e, t, sum in resultados
        ]

        return jsonify({"solicitudes": solicitudes_json})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/consultaReportesAlumno', methods=['GET'])
@token_required
def consultaReportesAlumno():
    alumno_id = request.args.get('alumno')
    if not alumno_id:   return "Usuario no enviado",400

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
        if not resultados:   return "No hay resultados",400

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


@app.route('/consultaReportesTodos', methods=['GET'])
@token_required
def consultaReportesTodos():
    try:
        #{todos, tipo}
        #filtro = request.args.get('filtro')
        tipo_solicitud = request.args.get('tipo')
        if tipo_solicitud == "todos":
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
            .filter(reporte.estado == 5)

        )
        else:
            tipoFiltro = (
                db.session.query(
                    tipo
                )
                .filter(tipo.tipo == tipo_solicitud)
                .first()
            )
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
                .filter(tipoFiltro.tipo == tipo_solicitud, reporte.estado == 5)
            )
        
        resultados = solicitudes.all()
        if not resultados:   return "No hay resultados",400

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
@token_required
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
        acceso= data.get('ver_pdf', False)
        #validador = data.get('validador')
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

        #solicitudExist.validador = validador

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
            return "Error: Esta solicitud ya existe",400
        
        # Verificar si la carpeta padre existe, y si no, crearla
        carpeta_padre = os.path.dirname(file_path)
        if not os.path.exists(carpeta_padre):
            os.makedirs(carpeta_padre)
        
        pdf_file.save(f"{ruta_carpeta}//{pdf_file.filename}")

        solicitudExist.estado = 1
        solicitudExist.carta_aceptacion = file_path
        solicitudExist.acceso_aceptacion = acceso
        db.session.commit()

        return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} aceptada correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/AceptarRechazarLiberacion', methods=['PATCH'])
@token_required
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
        acceso= data.get('ver_pdf', False)
        #validador = data.get('validador')
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


        if not solicitudExist:
            return "Solicitud no encontrada",400
        
        if estatus == "Rechazado":
            estatus = 4
            solicitudExist.estado = estatus
            db.session.commit()
            return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} suspendida correctamente"}), 200
        
        if estatus != "Aceptado":
            return jsonify({"mensaje": f"Estatus no valido"}), 400
        
        pdf_file = request.files['pdf']

        ruta_carpeta = f"../archivo/{alumnoReq.curp}/cartaLiberacion"
        file_path = f"{ruta_carpeta}/{pdf_file.filename}"
        solicitudExiste=(
            db.session.query(solicitud)
            .filter(solicitud.liberacion == file_path)
            .first()
        )
        if (solicitudExiste):
            return "Error: Esta solicitud ya existe",400
        
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
        solicitudExist.acceso_alumno =acceso

        db.session.commit()

        return jsonify({"mensaje": f"Solicitud con ID {solicitud_id} liberada correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/AceptarRechazarReporte', methods=['PATCH'])
@token_required
def AceptarRechazarReporte():
    try:
        data = request.get_json()
        #{"solicitud":"1","estatus":"Rechazado","validador":"8"}
        reporte_id = data.get('reporte')
        estatus = data.get('estatus')
        horas = data.get('horas')
        #estatus {Aceptado,Rechazado,Liberado,Suspendido,Pendiente}
        
        reporteExist=(
            db.session.query(reporte)
            .filter(reporte.id == reporte_id)
            .first()
        )
        if not reporteExist:    return "Este reporte no existe",400

        if estatus == "Aceptado":
            estado = 1
        elif estatus == "Rechazado":
            estado = 2
        else:
            return "Estatus no valido",400

        reporteExist.horas = horas
        reporteExist.estado = estado
        db.session.commit()

        return jsonify({"mensaje": f"Reporte con ID {reporte_id} modificado correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/alumnoAccedeLiberacion', methods=['PATCH'])
@token_required
def alumnoAccedeLiberacion():
    try:
        json_data_str = request.values.get('JSON')
        if json_data_str:
            data = json.loads(json_data_str)
        else:
            data = request.get_json(force=True)
        solicitud_id = data.get('solicitud')
        
        solicitudExist=(
            db.session.query(solicitud)
            .filter(solicitud.id == solicitud_id)
            .first()
        )

        if not solicitudExist:
            return "Solicitud no encontrada",400

        solicitudExist.acceso_alumno = True
        db.session.commit()

        return jsonify({"mensaje": f"El usisario ahora puede acceder"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/alumnos', methods=['GET'])
@token_required
def obtener_alumnos():
    try:
        alumnos = (
            db.session.query(alumno, usuarios, plantel, universidad)
            .join(usuarios, alumno.id == usuarios.id)
            .join(plantel, alumno.plantel == plantel.id)
            .join(universidad, plantel.universidad == universidad.id)
            .all()
        )

        alumnos_json = [
            {
                'id': alumno.id,
                'curp': alumno.curp,
                'carrera': alumno.carrera,
                'usuario': usuario.usuario,
                'contrasenia': usuario.contrasenia,
                'nombre': f"{usuario.nombre} {usuario.apellidop} {usuario.apellidom}",
                'plantel': plantel.nombre,
                'universidad': universidad.universidad,
            }
            for alumno, usuario, plantel, universidad in alumnos
        ]

        return jsonify({'alumnos': alumnos_json})

    except Exception as e:
        return str(e), 500

@app.route('/alumnoEditar', methods=['PATCH'])
@token_required
def alumnoEditar():
    try:
        data = request.get_json()
        alumno_input = data['alumno']
        curpN = data.get('curp')
        carrera = data.get('carrera')
        usuario = data.get('usuario')
        contrasenia = data.get('contrasenia')
        nombre = data.get('nombre')
        apellidop = data.get('apellidop')
        apellidom = data.get('apellidom')
        plantel_id = data.get('plantel')
        alumnos = (
            db.session.query(alumno, usuarios)
            .join(usuarios, alumno.id == usuarios.id)
            .filter(alumno.id == alumno_input)
            .first()
        )
        if alumnos is None: return "Alumno no encontrado"
        #print(alumnos[0].curp)
        #print(curpN)
        if curpN:   alumnos[0].curp = curpN
        if carrera: alumnos[0].carrera = carrera
        if usuario: alumnos[1].usuario = usuario
        if contrasenia: alumnos[1].contrasenia = contrasenia
        if nombre: alumnos[1].nombre = nombre
        if apellidop: alumnos[1].apellidop = apellidop
        if apellidom: alumnos[1].apellidom = apellidom
        if plantel_id: alumnos[1].plantel_id = plantel_id

        db.session.commit()
        return "Actualización completada",200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
        
@app.route('/planteles', methods=['GET'])
@token_required
def plantel_get():
    try:
        planteles = (
            db.session.query(plantel, universidad)
            .join(universidad, plantel.universidad == universidad.id)
            .all()
        )

        planteles_json = [
            {
                'id_plantel': plantel.id,
                'id_universidad': universidad.id,
                'universidad': universidad.universidad,
                'plantel': plantel.nombre
            }
            for plantel, universidad in planteles
        ]

        return jsonify(planteles_json)

    except Exception as e:
        return str(e), 500

@app.route('/dependencias', methods=['GET'])
@token_required
def dependencias_get():
    try:
        dependenciasAll = (
            db.session.query(dependencia, secretaria)
            .join(secretaria, secretaria.id == dependencia.secretaria)
            .all()
        )

        secretarias_json = [
            {
                'id_dependencia': dependencia.id,
                'id_secretaria': secretaria.id,
                'dependencia': dependencia.dependencia,
                'secretaria': secretaria.secretaria
            }
            for dependencia, secretaria in dependenciasAll
        ]

        return jsonify(secretarias_json)

    except Exception as e:
        return str(e), 500
    

@app.route('/dependenciaEditar', methods=['PATCH'])
@token_required
def dependenciaEditar():
    try:
        data = request.get_json()
        id_dependencia = data.get('dependencia')
        nombre = data.get('nombre')
        id_secretaria = data.get('secretaria')
        print(data)
        if not id_dependencia:  return "Error de dependencia",400

        dependencias = (
            db.session.query(dependencia)
            .filter(dependencia.id == id_dependencia)
            .first()
        )
        if dependencias is None: return "Dependencia no encontrada"
        #print(alumnos[0].curp)
        if nombre:  dependencias.dependencia = nombre
        if id_secretaria:   dependencias.secretaria = id_secretaria

        db.session.commit()
        return "Actualización completada",200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/agregarUniversidadPlantel', methods=['POST'])
@token_required
def agregarUniversidadPlantel():
    try:
        data = request.get_json()
        id_universidad = data.get('id_universidad')
        universidad_nombre = data.get('universidad_nombre')
        plantel_nombre = data.get('plantel_nombre')
        direccion = data.get('direccion')
        if id_universidad and plantel_nombre and direccion:
            nuevoPlantel = plantel()
            nuevoPlantel.activo = True
            nuevoPlantel.direccion = direccion
            nuevoPlantel.nombre = plantel_nombre
            nuevoPlantel.universidad = id_universidad
            db.session.add(nuevoPlantel)
            db.session.commit()
            return "Plantel agregado correctamente",200
        elif not universidad_nombre:
            return "Parametros de creación no validos",400
        nuevaUniversidad = universidad()
        nuevaUniversidad.activo = True
        nuevaUniversidad.universidad = universidad_nombre
        db.session.add(nuevaUniversidad)
        db.session.commit()
        return "Universidad creada correctamente",200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/generarQr', methods=['GET'])
@token_required
def generarQr():
    solicitud_id = request.args.get('solicitud')
    solicitudes = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.id == solicitud_id)
            .order_by(solicitud.fechasolicitud)
            .limit(1)
            )
    resultados = solicitudes.all()
    datos_qr = '\n'.join([
        f"https://servicioypracticas.hidalgo.gob.mx/datosQR/{s.sha}"
        for s, a, u, e, t in resultados
    ])
    #print(resultados[0][0].firma)
    cadena=f"{resultados[0][0].firma}|{resultados[0][0].fechaliberacion}|{resultados[0][0].fechasolicitud}|{resultados[0][0].fechasolicitud}|{resultados[0][0].firma}"
    firma_base64 = base64.b64encode(cadena.encode('utf-8')).decode('utf-8')
    hash_obj = hashlib.sha256(firma_base64.encode('utf-8'))

    firma = hash_obj.hexdigest()
    

    # Generar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    #url = f"http://localhost:3000/{url_params['nombre']} {url_params['apellidop']} {url_params['apellidom']}/{url_params['estado']}/{url_params['tipo']}/{url_params['firma']}/{url_params['fechaliberacion']}"
    qr.add_data(datos_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir la imagen a base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    anexo = (
            db.session.query(anexos)
            .filter(anexos.id == 1)
            .limit(1)
            ).first()

    # Enviar la respuesta JSON con la imagen base64
    response_data = {
        'solicitud_id': solicitud_id,
        'qr_image_base64': img_base64,
        'firma':firma*10,
        'firma_base64':anexo.anexo
    }

    return jsonify(response_data)

@app.route('/datosAceptacion', methods=['GET'])
@token_required
def datosAceptacion():
    try:
        solicitud_id = request.args.get('solicitud')
        solicitudes = (
                db.session.query(solicitud,alumno,usuarios,plantel,universidad)
                .join(alumno, alumno.id == solicitud.alumno)
                .join(usuarios, alumno.id == usuarios.id)
                #.join(proyectos, proyectos.id == solicitud.proyecto)
                .join(plantel, plantel.id == alumno.plantel)
                .join(universidad, universidad.id == plantel.universidad)
                .filter(solicitud.id == solicitud_id)
                .limit(1)
                )
        resultados = solicitudes.all()
        if not resultados:  return "Solicitud no encontrada",400
        #print(resultados)
        sol= resultados[0][0]
        curp = resultados[0][1].curp
        alum = resultados[0][1]
        us = resultados[0][2]
        #proyecto = resultados[0][3]
        plan=resultados[0][3]
        uni=resultados[0][4]
        response = {
            "alumno":f"{us.nombre} {us.apellidop} {us.apellidom}",
            "solicitud" : sol.id,
            "carrera": alum.carrera,
            "plantel": plan.nombre,
            "universidad": uni.universidad,
            "matricula":alum.matricula,
            "curp": curp,
        }
        return jsonify(response)
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/solicitarLiberacion', methods=['PATCH'])
@token_required
def solicitarLiberacion():
    solicitud_id = request.args.get('solicitud')
    try:
        solicitudes = (
                db.session.query(solicitud)
                .filter(solicitud.id == solicitud_id)
                .limit(1)
                .first()
                )
        
        if not solicitudes:
            return "Solicitud no encontrada",400
        
        solicitudes.estado=6
        db.session.commit()
        return "Liberacion solicitada",200


    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/idSolicitud', methods=['GET'])
@token_required
def idSolicitud():
    id_alumno = request.args.get('alumno')
    try:
        solicitudes = (
            db.session.query(solicitud)
            .filter(
                solicitud.alumno == id_alumno, 
                solicitud.fechaliberacion.is_(None),
                solicitud.carta_aceptacion.isnot(None),  
                solicitud.estado == 1
            )
            .order_by(solicitud.fechasolicitud)
            .limit(1)
            .first()
        )
        print(solicitudes)
        if not solicitudes:
            return "Ningina solicitud aplicable para liberación",400
        
        response={"id":solicitudes.id,}
        return jsonify(response)


    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/consultaProyectos', methods=['GET'])
@token_required
def consultaProyectos():
    #id_alumno = request.args.get('alumno')
    try:
        get_proyectos = (
            db.session.query(proyectos,dependencia)
            .outerjoin(dependencia,dependencia.id==proyectos.dependencia)
        ).all()
        #print(get_proyectos)
        if not get_proyectos:
            return "Ningin proyecto encontrado",400
        
        response = [{
            "id": proyecto.id,
            "proyecto": proyecto.nombre_proyecto,
            "dependencia": dependencia.dependencia if dependencia else None,
            "id_dependencia": dependencia.id if dependencia else None,
        } for proyecto, dependencia in get_proyectos]
        return jsonify(response)


    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/plantelEditar', methods=['PATCH'])
@token_required
def plantelEditar():
    try:
        data = request.get_json()
        nombre_plantel = data.get('plantel')
        nuevo_nombre = data.get('nuevo_plantel')
        print(data)
        if not (nombre_plantel and nuevo_nombre):  return "Error de datos enviados",400

        planteles = (
            db.session.query(plantel)
            .filter(plantel.nombre == nombre_plantel)
            .first()
        )
        if planteles is None: return "Plantel no encontrado",400
        print(planteles.nombre)
        planteles.nombre = nuevo_nombre
        #dependencias.secretaria = id_secretaria

        db.session.commit()
        return "Actualización completada",200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/agregar_dependencia', methods=['GET', 'POST'])
@token_required
def agregar_dependencia():
    try:
        data = request.get_json()
        dependencia_nombre = data.get('dependencia')
        #print(dependencia_nombre)
        secretaria_id = data.get('secretaria_id')
        secretarias = (
            db.session.query(secretaria)
            .filter(secretaria.id == secretaria_id)
            .first()
        )
        if not (secretaria_id and dependencia_nombre):
            return "Error: No se ha enviado los datos",500
        if not(secretarias):    return "Secretaria no encontrada",400
        print(secretarias)
        nueva_dependencia = dependencia(dependencia=dependencia_nombre, secretaria=secretarias.id)
        db.session.add(nueva_dependencia)
        db.session.commit()

        return "Dependencia agregada correctamente",200
    except Exception as e:
        db.session.rollback()
        return "Error: " + str(e),500
        
@app.route('/consultaQR', methods=['GET'])
@token_required
def consultaQR():
    try:
        #print(request)
        solicitud_sha = request.args.get('solicitud')
        #solicitud_sha = request.form['solicitud']
        #print(solicitud_sha)
        solicitud_consulta = (
            db.session.query(solicitud,alumno,usuarios,estado,tipo)
            .join(alumno, alumno.id == solicitud.alumno)
            .join(usuarios, alumno.id == usuarios.id)
            .join(estado, estado.id == solicitud.estado)
            .join(tipo, tipo.id == solicitud.tipo)
            .filter(solicitud.sha == solicitud_sha)
            .order_by(solicitud.fechasolicitud)
            .limit(1)
            ).all()
        
        if not solicitud_consulta:
            return {"respuesta":"No existe la solicitud"},404
        #print(solicitud_consulta)
        
        response = [
        {
            'nombre': f"{u.nombre} {u.apellidop} {u.apellidom}",
            'estado': e.estado,
            'tipo': t.tipo,
            'fecha_solicitud': s.fechasolicitud,
            'firma': s.firma if s.firma else "No hay una firma disponible",
            'fecha_liberacion': s.fechaliberacion if s.fechaliberacion else "N/A",
        }
            for s, a, u, e, t in solicitud_consulta
        ]
        #print(response)
        return jsonify(response)
    
    except Exception as e:
        db.session.rollback()
        return "Error: " + str(e),500
