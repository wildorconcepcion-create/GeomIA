from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(
        db.String(20),
        nullable=False,
        default="investigador"
    )

    def __repr__(self):
        return f"<Usuario {self.nombre}>"


class Evento(db.Model):
    __tablename__ = "eventos"

    id = db.Column(db.Integer, primary_key=True)
    nombre_evento = db.Column(db.String(150), nullable=False)
    tipo_evento = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.String(20))
    ubicacion = db.Column(db.String(150))
    descripcion = db.Column(db.Text)
    nivel_riesgo = db.Column(db.String(20))

    def __repr__(self):
        return f"<Evento {self.nombre_evento}>"