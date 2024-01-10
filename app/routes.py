from flask import render_template, jsonify, request
from app import app
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
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
            'rol': rolUsuario.rol
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
 
        return "Usuario y Alumno creados exitosamente."

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