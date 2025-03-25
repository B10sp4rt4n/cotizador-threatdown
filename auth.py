# auth.py
import sqlite3
import hashlib
from database import conectar_db

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def autenticar_usuario(correo, contrasena):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, tipo_usuario, admin_id FROM usuarios
        WHERE correo = ? AND contraseña = ?
    """, (correo, hash_password(contrasena)))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def crear_usuario(nombre, correo, contrasena, tipo_usuario, admin_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usuarios (nombre, correo, contraseña, tipo_usuario, admin_id)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, correo, hash_password(contrasena), tipo_usuario, admin_id))
    conn.commit()
    conn.close()

def actualizar_contrasena(correo, nueva_contrasena):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE usuarios SET contraseña = ? WHERE correo = ?
    """, (hash_password(nueva_contrasena), correo))
    conn.commit()
    conn.close()
